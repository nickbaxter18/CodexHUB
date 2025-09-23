"""Integration tests covering Agent, QAEngine, QAEventBus, and MetaAgent interactions."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import pytest

from agents.agent_base import Agent, AgentTaskError
from agents.meta_agent import MetaAgent
from qa.qa_engine import QAEngine, QARules
from qa.qa_event_bus import QAEventBus


class DummyAgent(Agent):
    """Lightweight agent used to simulate deterministic task outcomes for tests."""

    def __init__(
        self,
        name: str,
        qa_engine: QAEngine,
        event_bus: QAEventBus,
        metrics: Dict[str, Any],
        tests_executed: Optional[Sequence[str]] = None,
    ) -> None:
        super().__init__(name, qa_engine, event_bus)
        self._metrics = metrics
        self._tests_executed = list(tests_executed) if tests_executed is not None else None

    def perform_task(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        payload = dict(self._metrics)
        if self._tests_executed is not None:
            payload["tests_executed"] = list(self._tests_executed)
        return payload


@pytest.fixture()
def qa_engine_obj() -> QAEngine:
    """Provide a QAEngine loaded from the repository's bundled rules and schema."""

    base = Path(__file__).resolve().parent.parent
    rules = QARules.load_from_file(base / "qa" / "qa_rules.json", base / "qa" / "qa_rules.schema.json")
    return QAEngine(rules)


def test_agent_success_flow_emits_events(qa_engine_obj: QAEngine) -> None:
    """A successful agent run should emit success events and a positive arbitration decision."""

    bus = QAEventBus()
    MetaAgent(qa_engine_obj, bus)
    success_events: List[Dict[str, Any]] = []
    arbitration_events: List[Dict[str, Any]] = []

    bus.subscribe("qa_success", lambda event, data: success_events.append(data))
    bus.subscribe("qa_arbitration", lambda event, data: arbitration_events.append(data))

    agent = DummyAgent(
        "Frontend",
        qa_engine_obj,
        bus,
        {"lighthouse_score": 95, "accessibility_pass": True},
        tests_executed=qa_engine_obj.get_agent_tests("Frontend"),
    )
    result = agent.run_with_qa()

    assert result["qa_evaluation"].passed is True
    assert result["qa_evaluation_payload"]["tests_executed"] == qa_engine_obj.get_agent_tests("Frontend")
    assert result["qa_tests_executed"] == qa_engine_obj.get_agent_tests("Frontend")
    assert success_events and success_events[0]["status"] == "success"
    assert arbitration_events and arbitration_events[0]["decision"] == "success_recorded"
    assert arbitration_events[0]["conflict"] is False
    assert "qa_recommended_macros" not in result
    assert result["qa_evaluation"].metric_violations == []
    assert result["qa_severity_level"] == "none"
    assert result["qa_severity_score"] == 0.0
    assert "qa_untracked_metrics" not in result
    assert success_events[0]["severity_level"] == "none"
    assert arbitration_events[0]["severity_level"] == "none"
    assert success_events[0]["tests_executed"] == qa_engine_obj.get_agent_tests("Frontend")
    assert arbitration_events[0]["tests_executed"] == qa_engine_obj.get_agent_tests("Frontend")


def test_agent_failure_triggers_remediation(qa_engine_obj: QAEngine) -> None:
    """Failing metrics should produce remediation guidance and arbitration next steps."""

    bus = QAEventBus()
    MetaAgent(qa_engine_obj, bus)
    arbitration_events: List[Dict[str, Any]] = []
    bus.subscribe("qa_arbitration", lambda event, data: arbitration_events.append(data))

    agent = DummyAgent(
        "Frontend",
        qa_engine_obj,
        bus,
        {"lighthouse_score": 10, "accessibility_pass": False},
        tests_executed=["jest_unit"],
    )
    result = agent.run_with_qa()

    assert result["qa_evaluation"].passed is False
    assert arbitration_events
    decision = arbitration_events[-1]
    assert decision["decision"] == "tests_required"
    assert decision["missing_tests"]
    assert decision["next_steps"]
    assert "::frontendgen-access" in result["qa_recommended_macros"]
    assert "::frontendgen-access" in decision["recommended_macros"]
    assert result["qa_severity_level"] in {"medium", "high"}
    assert result["qa_severity_score"] > 0
    assert decision["severity_level"] in {"medium", "high"}
    assert decision["severity"] >= result["qa_severity_score"]
    assert decision.get("untracked_metrics", []) == []
    assert result["qa_tests_executed"] == ["jest_unit"]
    assert decision["tests_executed"] == ["jest_unit"]


def test_meta_agent_medium_severity_prompts_remediation(qa_engine_obj: QAEngine) -> None:
    """Medium-severity failures without missing tests should trigger remediation decisions."""

    bus = QAEventBus()
    MetaAgent(qa_engine_obj, bus)
    arbitration_events: List[Dict[str, Any]] = []
    bus.subscribe("qa_arbitration", lambda event, data: arbitration_events.append(data))

    agent = DummyAgent(
        "Frontend",
        qa_engine_obj,
        bus,
        {"lighthouse_score": 75, "accessibility_pass": True},
        tests_executed=qa_engine_obj.get_agent_tests("Frontend"),
    )
    result = agent.run_with_qa()

    assert arbitration_events, "Expected arbitration decision"
    decision = arbitration_events[-1]
    assert decision["decision"] == "remediation_required"
    assert decision["severity_level"] == "medium"
    assert decision["severity"] == pytest.approx(result["qa_severity_score"], rel=1e-6)
    assert "Execute required QA tests" not in " ".join(decision.get("next_steps", []))
    assert decision["tests_executed"] == qa_engine_obj.get_agent_tests("Frontend")


def test_meta_agent_detects_conflicting_signals(qa_engine_obj: QAEngine) -> None:
    """When success is followed by failure, the MetaAgent should flag a conflict and escalate."""

    bus = QAEventBus()
    MetaAgent(qa_engine_obj, bus)
    arbitration_events: List[Dict[str, Any]] = []
    bus.subscribe("qa_arbitration", lambda event, data: arbitration_events.append(data))

    success_agent = DummyAgent(
        "Frontend",
        qa_engine_obj,
        bus,
        {"lighthouse_score": 95, "accessibility_pass": True},
        tests_executed=qa_engine_obj.get_agent_tests("Frontend"),
    )
    success_agent.run_with_qa()

    failing_agent = DummyAgent(
        "Frontend",
        qa_engine_obj,
        bus,
        {"lighthouse_score": 70, "accessibility_pass": False},
        tests_executed=qa_engine_obj.get_agent_tests("Frontend"),
    )
    failing_agent.run_with_qa()

    assert len(arbitration_events) >= 2
    last_decision = arbitration_events[-1]
    assert last_decision["conflict"] is True
    assert last_decision["decision"] == "escalate_for_review"
    assert "next_steps" in last_decision
    assert "::frontendgen-access" in last_decision["recommended_macros"]
    assert last_decision["severity_level"] in {"medium", "high"}
    assert last_decision["severity"] > 0
    assert last_decision["tests_executed"] == qa_engine_obj.get_agent_tests("Frontend")


def test_agent_exception_publishes_failure(qa_engine_obj: QAEngine) -> None:
    """Exceptions raised during task execution should emit QA failure events and evaluations."""

    bus = QAEventBus()
    MetaAgent(qa_engine_obj, bus)
    failure_events: List[Dict[str, Any]] = []
    arbitration_events: List[Dict[str, Any]] = []

    bus.subscribe("qa_failure", lambda event, data: failure_events.append(data))
    bus.subscribe("qa_arbitration", lambda event, data: arbitration_events.append(data))

    class ErrorAgent(Agent):
        def perform_task(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
            raise RuntimeError("calculation failed")

    agent = ErrorAgent("Frontend", qa_engine_obj, bus)

    with pytest.raises(AgentTaskError) as excinfo:
        agent.run_with_qa()

    evaluation = excinfo.value.evaluation
    assert evaluation.passed is False
    assert evaluation.error == {"type": "RuntimeError", "message": "calculation failed"}

    assert failure_events, "Expected failure event to be published"
    failure_payload = failure_events[-1]
    assert failure_payload["error"]["type"] == "RuntimeError"
    assert not evaluation.passed
    assert "::frontendgen-access" in failure_payload.get("remediation_macros", [])
    assert failure_payload["severity_level"] in {"medium", "high"}
    assert failure_payload["severity"] >= 1.0
    assert failure_payload["tests_executed"] == []

    assert arbitration_events, "Expected arbitration decision to be produced"
    arbitration_payload = arbitration_events[-1]
    assert arbitration_payload["decision"] in {"failure_recorded", "tests_required"}
    assert "::frontendgen-access" in arbitration_payload.get("recommended_macros", [])
    assert arbitration_payload["severity_level"] in {"medium", "high"}
    assert arbitration_payload["severity"] >= 1.0
    assert arbitration_payload["tests_executed"] == []
