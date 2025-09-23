"""Meta Agent v2 orchestrates arbitration, trust, drift detection, fallbacks, and macros."""

# === Imports / Dependencies ===
from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from .arbitration_engine import ArbitrationDecision, ArbitrationEngine
from .drift_detector import DriftDetector
from .fallback_manager import FallbackManager
from .macro_dependency_manager import MacroDependencyManager, MacroState
from .qa_event_bus import QAEventBus
from .trust_engine import TrustEngine


logger = logging.getLogger(__name__)


# === Types, Interfaces, Contracts, Schema ===
class MetaAgent:
    """Executive layer that coordinates subsystem engines for QA governance."""

    def __init__(
        self,
        trust_engine: TrustEngine,
        arbitration_engine: ArbitrationEngine,
        drift_detector: DriftDetector,
        fallback_manager: FallbackManager,
        macro_manager: MacroDependencyManager,
        event_bus: QAEventBus,
        arbitration_log_path: Optional[Path] = None,
    ) -> None:
        self.trust_engine = trust_engine
        self.arbitration_engine = arbitration_engine
        self.drift_detector = drift_detector
        self.fallback_manager = fallback_manager
        self.macro_manager = macro_manager
        self.event_bus = event_bus
        self._lock = threading.RLock()
        self._arbitration_log_path = (
            arbitration_log_path if arbitration_log_path is not None else Path("logs/arbitrations.jsonl")
        )
        self._arbitration_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.event_bus.subscribe("qa_failure", self.handle_event)
        self.event_bus.subscribe("qa_success", self.handle_event)
        self.event_bus.subscribe("macro_definition", self.handle_event)
        self.event_bus.subscribe("macro_dependency_update", self.handle_event)

    def handle_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Route events to QA processing, macro tracking, or ignore unknown types."""

        if event_type in {"qa_failure", "qa_success"}:
            self._process_qa_event(event_type, data)
        elif event_type == "macro_definition":
            self._process_macro_definition(data)
        elif event_type == "macro_dependency_update":
            self._process_dependency_update(data)

    def propose_rule_update(self) -> Dict[str, Any]:
        """Expose accumulated drift proposals for human/architect review."""

        proposals = self.drift_detector.get_proposals()
        return {"proposals": proposals}

    # === Core Logic / Implementation ===
    def _process_qa_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Process QA events: update trust, arbitrate conflicts, and manage drift."""

        sanitized = self._sanitize_event_payload(data)
        if not sanitized:
            return
        correlation_id = sanitized["correlation_id"]
        agent = sanitized.get("agent")
        metric = sanitized.get("metric")
        status = sanitized.get("status") or self._infer_status(event_type)
        value = sanitized.get("value")
        threshold = sanitized.get("threshold")
        event_record = {
            "agent": agent,
            "metric": metric,
            "status": status,
            "value": value,
            "threshold": threshold,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "correlation_id": correlation_id,
        }
        conflicts: Optional[Iterable[Dict[str, Any]]] = None
        trust_snapshot: Dict[str, float] = {}
        drift_triggered = False
        trigger_fallback = metric is not None and value is not None and threshold is not None
        with self._lock:
            self._update_trust(agent, status)
            trust_snapshot = self.trust_engine.get_trust_scores()
            self.drift_detector.record_event(agent, metric, status or "unknown")
            if metric:
                self.arbitration_engine.add_event(event_record)
                conflicts = self.arbitration_engine.collect_ready_conflicts(metric)
            drift_triggered = self.drift_detector.is_drift()
        if conflicts:
            decision = self.arbitration_engine.resolve_conflict(list(conflicts), trust_snapshot)
            decision_payload = self._build_arbitration_payload(decision, trust_snapshot, correlation_id)
            self._record_arbitration(decision_payload)
            self._publish("qa_arbitration", decision_payload, correlation_id)
        if drift_triggered:
            try:
                amendment = self.drift_detector.propose_amendment()
            except RuntimeError:
                amendment = None
            if amendment:
                amendment["correlation_id"] = correlation_id
                self._publish("qa_drift", amendment, correlation_id)
        if trigger_fallback and value is not None and threshold is not None and metric is not None:
            self.fallback_manager.evaluate_and_trigger(metric, value, threshold)

    def _process_macro_definition(self, data: Dict[str, Any]) -> None:
        """Register macro schemas and broadcast their compatibility state."""

        sanitized = self._sanitize_macro_definition(data)
        macro = sanitized.get("macro")
        dependencies = sanitized.get("dependencies", {})
        schema_version = sanitized.get("schema_version")
        if not macro:
            return
        correlation_id = sanitized.get("correlation_id", str(uuid.uuid4()))
        with self._lock:
            state = self.macro_manager.register_macro(macro, schema_version, dependencies)
        self._broadcast_macro_states([state], correlation_id)

    def _process_dependency_update(self, data: Dict[str, Any]) -> None:
        """Update dependency schema versions and notify impacted macros."""

        sanitized = self._sanitize_dependency_update(data)
        dependency = sanitized.get("dependency")
        schema_version = sanitized.get("schema_version")
        if not dependency or schema_version is None:
            return
        correlation_id = sanitized.get("correlation_id", str(uuid.uuid4()))
        with self._lock:
            impacted = self.macro_manager.update_dependency_schema(dependency, schema_version)
        if impacted:
            self._broadcast_macro_states(impacted, correlation_id)

    def _update_trust(self, agent: Optional[str], status: Optional[str]) -> None:
        if not agent:
            return
        if status == "fail":
            self.trust_engine.record_failure(agent)
        elif status == "pass":
            self.trust_engine.record_success(agent)

    def _record_arbitration(self, decision: Dict[str, Any]) -> None:
        try:
            with self._arbitration_log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(decision, sort_keys=True))
                handle.write("\n")
        except OSError as exc:
            logger.error("Failed to persist arbitration decision: %s", exc)
            warning_payload = {
                "error": str(exc),
                "decision": decision,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            correlation = decision.get("correlation_id", str(uuid.uuid4()))
            self._publish("qa_arbitration_log_error", warning_payload, correlation)

    def _broadcast_macro_states(self, states: Iterable[MacroState], correlation_id: Optional[str] = None) -> None:
        """Publish macro states and emit block/unblock signals for orchestration."""

        for state in states:
            payload = self._macro_state_payload(state, correlation_id)
            corr = payload.get("correlation_id", str(uuid.uuid4()))
            self._publish("macro_state", payload, corr)
            event_name = "macro_blocked" if state.blocked else "macro_unblocked"
            self._publish(event_name, payload, corr)

    def _sanitize_event_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, Mapping):
            return {}
        sanitized: Dict[str, Any] = {"correlation_id": str(data.get("correlation_id") or uuid.uuid4())}
        agent = data.get("agent")
        if isinstance(agent, str) and agent.strip():
            sanitized["agent"] = agent.strip()
        metric = data.get("metric")
        if isinstance(metric, str) and metric.strip():
            sanitized["metric"] = metric.strip()
        status = data.get("status")
        if isinstance(status, str) and status.strip():
            normalized_status = self._normalize_status(status)
            if normalized_status:
                sanitized["status"] = normalized_status
        value = self._coerce_float(data.get("value"))
        if value is not None:
            sanitized["value"] = value
        threshold = self._coerce_float(data.get("threshold"))
        if threshold is not None:
            sanitized["threshold"] = threshold
        return sanitized

    @staticmethod
    def _sanitize_macro_definition(data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, Mapping):
            return {}
        allowed_keys = {"macro", "schema_version", "dependencies"}
        sanitized = {key: data.get(key) for key in allowed_keys}
        dependencies = sanitized.get("dependencies")
        if isinstance(dependencies, Mapping):
            sanitized["dependencies"] = {str(dep): str(version) for dep, version in dependencies.items()}
        else:
            sanitized["dependencies"] = {}
        schema_version = sanitized.get("schema_version")
        if schema_version is not None:
            sanitized["schema_version"] = str(schema_version)
        sanitized["correlation_id"] = str(data.get("correlation_id") or uuid.uuid4())
        return sanitized

    @staticmethod
    def _sanitize_dependency_update(data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, Mapping):
            return {}
        allowed_keys = {"dependency", "schema_version"}
        sanitized = {key: data.get(key) for key in allowed_keys}
        dependency = sanitized.get("dependency")
        if dependency is not None:
            sanitized["dependency"] = str(dependency)
        schema_version = sanitized.get("schema_version")
        if schema_version is not None:
            sanitized["schema_version"] = str(schema_version)
        sanitized["correlation_id"] = str(data.get("correlation_id") or uuid.uuid4())
        return sanitized

    @staticmethod
    def _infer_status(event_type: str) -> str:
        if event_type == "qa_failure":
            return "fail"
        if event_type == "qa_success":
            return "pass"
        return "unknown"

    @staticmethod
    def _normalize_status(status: str) -> Optional[str]:
        normalized = status.strip().lower()
        mapping = {
            "pass": "pass",
            "passed": "pass",
            "success": "pass",
            "succeeded": "pass",
            "ok": "pass",
            "fail": "fail",
            "failed": "fail",
            "failure": "fail",
            "error": "fail",
            "disabled": "disabled",
        }
        return mapping.get(normalized, normalized or None)

    def _coerce_float(self, value: Any) -> Optional[float]:
        if isinstance(value, (int, float)):
            return float(value)
        return None

    def _build_arbitration_payload(
        self,
        decision: ArbitrationDecision,
        trust_snapshot: Dict[str, float],
        correlation_id: str,
    ) -> Dict[str, Any]:
        rationale = dict(decision.rationale)
        top_weight = rationale.get("scores", [{}])[0].get("weight", 0.0) if rationale.get("scores") else 0.0
        second_weight = rationale.get("scores", [{}])[1].get("weight", 0.0) if len(rationale.get("scores", [])) > 1 else 0.0
        rationale["trust_gap"] = top_weight - second_weight
        payload = {
            "metric": decision.metric,
            "winner": decision.winner,
            "participants": decision.participants,
            "rationale": rationale,
            "trust_snapshot": trust_snapshot,
            "decided_at": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
        }
        return payload

    def _macro_state_payload(self, state: MacroState, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "macro": state.macro,
            "schema_version": state.schema_version,
            "dependencies": state.dependencies,
            "blocked": state.blocked,
            "reason": state.reason,
            "diff": state.diff,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id or str(uuid.uuid4()),
        }
        return payload

    def _publish(self, event_type: str, payload: Dict[str, Any], correlation_id: str) -> None:
        enriched = dict(payload)
        enriched.setdefault("correlation_id", correlation_id)
        self.event_bus.publish(event_type, enriched, correlation_id=correlation_id)


# === Error & Edge Case Handling ===
# Unknown agents are ignored by the trust engine; missing metrics skip arbitration and fallbacks.
# Macro definitions without names are ignored; dependency updates require dependency and schema values.
# Arbitration log failures emit a diagnostic event for downstream observability.


# === Performance / Resource Considerations ===
# Thread-safe updates rely on an ``RLock`` covering trust and macro state mutations. The asynchronous event
# bus prevents slow subscribers from blocking arbitration, and arbitration logs append JSON lines for audit
# trails while macro states emit targeted updates with diff metadata.


# === Exports / Public API ===
__all__ = ["MetaAgent"]
