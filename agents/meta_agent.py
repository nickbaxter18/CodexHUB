"""
SECTION: Header & Purpose
    - Implements the ``MetaAgent`` responsible for arbitrating QA signals and coordinating trust updates.
    - Listens to QA event bus topics, enforces missing-test escalations, weighs severity scoring, tracks error payloads,
      and publishes consolidated arbitration outcomes.

SECTION: Imports / Dependencies
    - Depends on the shared QA engine and event bus modules only.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from qa.qa_engine import QAEngine
from qa.qa_event_bus import QAEventBus


class MetaAgent:
    """Observer that aggregates QA events, updates trust, and publishes arbitration decisions."""

    def __init__(self, qa_engine: QAEngine, event_bus: QAEventBus) -> None:
        self.qa_engine = qa_engine
        self.event_bus = event_bus
        self.arbitration_memory: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self.agent_last_event: Dict[str, Dict[str, Any]] = {}
        self.event_bus.subscribe("qa_failure", self.handle_qa_failure)
        self.event_bus.subscribe("qa_success", self.handle_qa_success)

    def handle_qa_failure(self, event_type: str, data: Dict[str, Any]) -> None:
        """Process QA failure events and publish an arbitration decision."""

        evaluation = self._normalise_event_payload(data, passed=False)
        resolution = self._arbitrate(evaluation, event_type)
        self.event_bus.publish("qa_arbitration", resolution)

    def handle_qa_success(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record a QA success event and publish the resulting arbitration decision."""

        evaluation = self._normalise_event_payload(data, passed=True)
        resolution = self._arbitrate(evaluation, event_type)
        self.event_bus.publish("qa_arbitration", resolution)

    def _normalise_event_payload(self, data: Dict[str, Any], passed: bool) -> Dict[str, Any]:
        """Ensure event payloads contain the standard fields used for arbitration."""

        agent = data.get("agent", "unknown")
        metrics = dict(data.get("metrics", {}))
        violations = list(data.get("violations", []))
        remediation = list(data.get("remediation", []))
        missing_tests = list(data.get("missing_tests", []))
        tests_executed = list(data.get("tests_executed", []))
        trust = data.get("trust", self.qa_engine.get_agent_trust(agent))
        failure_history = list(data.get("failure_history", []))
        error = data.get("error") if data.get("error") else None
        recommended_macros = list(data.get("remediation_macros", []))
        metric_violations = list(data.get("metric_violations", []))
        severity = float(data.get("severity", 0.0))
        severity_level = str(data.get("severity_level", "none"))
        untracked_metrics = list(data.get("untracked_metrics", []))

        payload = {
            "agent": agent,
            "status": "success" if passed else "failure",
            "metrics": metrics,
            "violations": violations,
            "remediation": remediation,
            "missing_tests": missing_tests,
            "tests_executed": tests_executed,
            "trust": trust,
            "failure_history": failure_history,
            "error": error,
            "recommended_macros": recommended_macros,
            "metric_violations": metric_violations,
            "severity": severity,
            "severity_level": severity_level,
            "untracked_metrics": untracked_metrics,
        }
        return payload

    def _arbitrate(self, evaluation: Dict[str, Any], event_type: str) -> Dict[str, Any]:
        """Resolve the latest QA signal against historical context and emit a decision."""

        agent = evaluation["agent"]
        previous: Optional[Dict[str, Any]] = self.agent_last_event.get(agent)
        conflict = bool(previous) and previous.get("status") != evaluation.get("status")
        missing_tests = evaluation.get("missing_tests", [])
        severity = float(evaluation.get("severity", 0.0))
        severity_level = str(evaluation.get("severity_level", "none"))
        untracked_metrics = list(evaluation.get("untracked_metrics", []))

        if missing_tests:
            decision = "tests_required"
        elif severity_level == "high":
            decision = "escalate_for_review"
        elif severity_level == "medium" and evaluation["status"] == "failure":
            decision = "remediation_required"
        elif conflict and evaluation["status"] == "failure":
            decision = "escalate_for_review"
        elif conflict and evaluation["status"] == "success":
            decision = "recovery_confirmed"
        elif evaluation["status"] == "failure":
            decision = "failure_recorded"
        else:
            decision = "success_recorded"

        recommended_macros = evaluation.get("recommended_macros", [])
        resolution = {
            "agent": agent,
            "decision": decision,
            "status": evaluation["status"],
            "trust": evaluation.get("trust", self.qa_engine.get_agent_trust(agent)),
            "conflict": conflict,
            "previous_event": previous,
            "violations": evaluation.get("violations", []),
            "remediation": evaluation.get("remediation", []),
            "missing_tests": missing_tests,
            "tests_executed": evaluation.get("tests_executed", []),
            "event_type": event_type,
            "error": evaluation.get("error"),
            "recommended_macros": recommended_macros,
            "metric_violations": evaluation.get("metric_violations", []),
            "severity": severity,
            "severity_level": severity_level,
            "untracked_metrics": untracked_metrics,
        }

        memory_key = (agent, evaluation["status"])
        self.arbitration_memory[memory_key] = {
            "decision": decision,
            "trust": resolution["trust"],
            "conflict": conflict,
            "metrics": evaluation.get("metrics", {}),
            "missing_tests": missing_tests,
            "tests_executed": evaluation.get("tests_executed", []),
            "recommended_macros": recommended_macros,
            "severity": severity,
        }
        self.agent_last_event[agent] = evaluation

        next_steps: List[str] = []
        if evaluation["status"] == "failure" and evaluation.get("remediation"):
            next_steps.extend(evaluation.get("remediation", []))
        if missing_tests:
            next_steps.append(
                "Execute required QA tests: " + ", ".join(sorted(set(missing_tests)))
            )
        if recommended_macros:
            next_steps.append(
                "Trigger remediation macros: " + ", ".join(sorted(set(recommended_macros)))
            )
        if untracked_metrics:
            next_steps.append(
                "Define QA coverage for untracked metrics: "
                + ", ".join(sorted(set(untracked_metrics)))
            )
        if severity_level in {"medium", "high"} and evaluation["status"] == "failure":
            next_steps.append(
                f"Review severity level '{severity_level}' impact with Macro & QA coordinators"
            )
        if next_steps:
            resolution["next_steps"] = next_steps

        return resolution
