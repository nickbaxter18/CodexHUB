"""Integration tests for MetaAgent v2 orchestration."""

# === Imports / Dependencies ===
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from meta_agent.arbitration_engine import ArbitrationEngine
from meta_agent.config_loader import ConfigLoader
from meta_agent.drift_detector import DriftDetector
from meta_agent.fallback_manager import FallbackManager
from meta_agent.logger import Logger
from meta_agent.macro_dependency_manager import MacroDependencyManager
from meta_agent.meta_agent_v2 import MetaAgent
from meta_agent.qa_event_bus import QAEventBus
from meta_agent.trust_engine import TrustEngine


# === Fixtures ===
@pytest.fixture()
def meta_stack(tmp_path: Path) -> Dict[str, object]:
    """Construct a MetaAgent with in-memory dependencies for tests."""

    trust_path = tmp_path / "trust.json"
    log_path = tmp_path / "arbitrations.jsonl"
    fallback_calls: List[Tuple[float, float]] = []

    def latency_fallback(value: float, threshold: float) -> None:
        fallback_calls.append((value, threshold))

    trust_engine = TrustEngine(trust_path)
    arbitration = ArbitrationEngine()
    drift = DriftDetector(window_size=3, threshold=2)
    fallback = FallbackManager({"latency": latency_fallback})
    macro_manager = MacroDependencyManager()
    bus = QAEventBus()
    logger = Logger(log_dir=tmp_path)
    agent = MetaAgent(
        trust_engine,
        arbitration,
        drift,
        fallback,
        macro_manager,
        bus,
        logger,
        arbitration_log_path=log_path,
    )
    return {
        "agent": agent,
        "bus": bus,
        "fallback_calls": fallback_calls,
        "log_path": log_path,
        "macro_manager": macro_manager,
    }


# === Tests ===


def test_arbitration_prefers_high_trust(meta_stack: Dict[str, object]) -> None:
    """When conflicts arise, the higher-trust agent should win the decision."""

    bus: QAEventBus = meta_stack["bus"]  # type: ignore[assignment]
    agent: MetaAgent = meta_stack["agent"]  # type: ignore[assignment]
    decisions: List[Dict[str, Any]] = []
    bus.subscribe("qa_arbitration", lambda event_type, payload: decisions.append(payload))
    agent.trust_engine.trust_scores.update({"alpha": 1.2, "beta": 0.8})
    bus.publish(
        "qa_failure",
        {"agent": "beta", "metric": "latency", "value": 320.0, "threshold": 300.0},
    )
    bus.publish(
        "qa_success",
        {"agent": "alpha", "metric": "latency", "value": 250.0, "threshold": 300.0},
    )
    assert bus.wait_for_idle(timeout=1.0)
    assert decisions, "Arbitration decision should be emitted"
    assert decisions[-1]["winner"] == "alpha"
    assert decisions[-1]["rationale"]["confidence"] >= 0
    log_path: Path = meta_stack["log_path"]  # type: ignore[assignment]
    assert log_path.exists()
    log_entries = [line for line in log_path.read_text().splitlines() if line.strip()]
    assert any('"winner": "alpha"' in entry for entry in log_entries)


def test_trust_updates_on_failure_and_success(meta_stack: Dict[str, object]) -> None:
    """MetaAgent should adjust trust after failure and success events."""

    bus: QAEventBus = meta_stack["bus"]  # type: ignore[assignment]
    agent: MetaAgent = meta_stack["agent"]  # type: ignore[assignment]
    initial = agent.trust_engine.get_trust_scores().get("gamma", 1.0)
    bus.publish(
        "qa_failure",
        {"agent": "gamma", "metric": "accuracy", "value": 0.5, "threshold": 0.9},
    )
    assert bus.wait_for_idle(timeout=1.0)
    after_failure = agent.trust_engine.get_trust_scores()["gamma"]
    assert after_failure < initial
    bus.publish(
        "qa_success",
        {"agent": "gamma", "metric": "accuracy", "value": 0.95, "threshold": 0.9},
    )
    assert bus.wait_for_idle(timeout=1.0)
    after_success = agent.trust_engine.get_trust_scores()["gamma"]
    assert after_success > after_failure


def test_success_synonym_updates_trust(meta_stack: Dict[str, object]) -> None:
    """Status synonyms like 'success' should promote trust just like 'pass'."""

    bus: QAEventBus = meta_stack["bus"]  # type: ignore[assignment]
    agent: MetaAgent = meta_stack["agent"]  # type: ignore[assignment]
    initial = agent.trust_engine.get_trust_scores().get("theta", 1.0)
    bus.publish(
        "qa_success",
        {
            "agent": "theta",
            "metric": "accuracy",
            "value": 0.98,
            "threshold": 0.9,
            "status": "success",
        },
    )
    assert bus.wait_for_idle(timeout=1.0)
    after_success = agent.trust_engine.get_trust_scores()["theta"]
    assert after_success > initial


def test_macro_dependency_blocking(meta_stack: Dict[str, object]) -> None:
    """Macro manager should block on incompatibility and unblock when schemas align."""

    bus: QAEventBus = meta_stack["bus"]  # type: ignore[assignment]
    agent: MetaAgent = meta_stack["agent"]  # type: ignore[assignment]
    states: List[Dict[str, Any]] = []
    bus.subscribe(
        "macro_blocked", lambda event_type, payload: states.append({"event": event_type, **payload})
    )
    bus.subscribe(
        "macro_unblocked",
        lambda event_type, payload: states.append({"event": event_type, **payload}),
    )

    bus.publish(
        "macro_definition",
        {
            "macro": "reporting",
            "schema_version": "1.0",
            "dependencies": {"inventory": "2.0"},
        },
    )
    assert bus.wait_for_idle(timeout=1.0)
    assert states, "Macro definition should emit a state event"
    assert states[-1]["event"] == "macro_blocked"
    assert states[-1]["reason"] == "dependency inventory schema unknown"
    assert agent.macro_manager.is_blocked("reporting")

    bus.publish("macro_dependency_update", {"dependency": "inventory", "schema_version": "2.0"})
    assert bus.wait_for_idle(timeout=1.0)
    assert states[-1]["event"] == "macro_unblocked"
    assert agent.macro_manager.is_blocked("reporting") is False

    bus.publish("macro_dependency_update", {"dependency": "inventory", "schema_version": "3.0"})
    assert bus.wait_for_idle(timeout=1.0)
    assert states[-1]["event"] == "macro_blocked"
    assert "schema mismatch" in str(states[-1]["reason"])


def test_drift_detection_emits_proposal(meta_stack: Dict[str, object]) -> None:
    """Repeated failures should publish a drift amendment proposal."""

    bus: QAEventBus = meta_stack["bus"]  # type: ignore[assignment]
    drift_events: List[Dict[str, Any]] = []
    bus.subscribe("qa_drift", lambda event_type, payload: drift_events.append(payload))
    bus.publish(
        "qa_failure",
        {"agent": "delta", "metric": "latency", "value": 340.0, "threshold": 300.0},
    )
    bus.publish(
        "qa_failure",
        {"agent": "delta", "metric": "latency", "value": 360.0, "threshold": 300.0},
    )
    assert bus.wait_for_idle(timeout=1.0)
    assert drift_events
    proposal = drift_events[-1]
    assert proposal["reason"] == "repeated test failures"
    assert proposal["metric"] == "latency"
    assert "severity" in proposal


def test_fallback_trigger_invoked(meta_stack: Dict[str, object]) -> None:
    """Fallback manager should be invoked when thresholds are exceeded."""

    bus: QAEventBus = meta_stack["bus"]  # type: ignore[assignment]
    fallback_calls: List[Tuple[float, float]] = meta_stack["fallback_calls"]  # type: ignore[assignment]
    bus.publish(
        "qa_failure",
        {"agent": "epsilon", "metric": "latency", "value": 400.0, "threshold": 300.0},
    )
    assert bus.wait_for_idle(timeout=1.0)
    assert fallback_calls == [(400.0, 300.0)]


def test_from_config_builder(tmp_path: Path) -> None:
    """MetaAgent.from_config should wire dependencies using governance files."""

    config_loader = ConfigLoader(config_dir=Path("config"))
    bus = QAEventBus()
    agent = MetaAgent.from_config(
        config_loader,
        bus,
        trust_store=tmp_path / "trust.json",
        log_dir=tmp_path,
    )
    assert agent.expose_trust()
