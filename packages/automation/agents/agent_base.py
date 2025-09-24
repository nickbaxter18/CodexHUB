"""
SECTION: Header & Purpose
    - Defines an abstract ``Agent`` base class that encapsulates QA enforcement behaviour for agent workflows.
    - Provides integration hooks for the shared ``QAEngine`` and ``QAEventBus`` components.
    - Normalises reported QA metrics, enforces execution of mandatory regression tests, captures task exceptions,
      and forwards severity/untracked-metric insights to orchestrators.

SECTION: Imports / Dependencies
    - Imports typing helpers alongside the shared QA modules.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from qa.qa_engine import QAEngine, QAEvaluation
from qa.qa_event_bus import QAEventBus


class AgentTaskError(RuntimeError):
    """Exception raised when ``perform_task`` fails; carries the QA evaluation context."""

    def __init__(self, agent: str, original: BaseException, evaluation: QAEvaluation) -> None:
        message = f"Agent '{agent}' task execution failed: {original}"
        super().__init__(message)
        self.agent = agent
        self.original = original
        self.evaluation = evaluation


class Agent:
    """Abstract base class representing an autonomous agent participating in QA governance."""

    def __init__(self, name: str, qa_engine: QAEngine, event_bus: QAEventBus) -> None:
        self.name = name
        self.qa_engine = qa_engine
        self.event_bus = event_bus

    def perform_task(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute the agent-specific task and return a dictionary of resulting metrics/data."""

        raise NotImplementedError("Subclasses must implement perform_task")

    def run_with_qa(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Run ``perform_task`` and automatically evaluate the output against QA budgets."""

        try:
            result = self.perform_task(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - intentional broad catch for QA recording
            evaluation = self.qa_engine.assess_exception(self.name, exc)
            payload = evaluation.to_event_payload()
            if not payload.get("error"):
                payload["error"] = {"type": exc.__class__.__name__, "message": str(exc)}
            self.event_bus.publish("qa_failure", payload)
            raise AgentTaskError(self.name, exc, evaluation) from exc

        if not isinstance(result, dict):
            raise TypeError("Agent perform_task must return a dictionary of metrics and data")

        tests_executed: Optional[Sequence[str]] = None
        if "tests_executed" in result:
            tests_value = result["tests_executed"]
            if tests_value is None:
                tests_executed = None
            elif isinstance(tests_value, Sequence) and not isinstance(tests_value, (str, bytes)):
                tests_executed = [str(test) for test in tests_value]
            else:
                raise TypeError(
                    "tests_executed must be an iterable of test identifiers when provided"
                )

        evaluation = self.qa_engine.assess_task_result(
            self.name, dict(result), tests_executed=tests_executed
        )

        event_type = "qa_success" if evaluation.passed else "qa_failure"
        self.event_bus.publish(event_type, evaluation.to_event_payload())

        if evaluation.violations:
            result.setdefault("qa_failures", []).extend(evaluation.violations)
        if evaluation.missing_tests:
            result.setdefault("qa_missing_tests", []).extend(evaluation.missing_tests)
        if evaluation.remediation_macros:
            existing_macros = result.setdefault("qa_recommended_macros", [])
            for macro in evaluation.remediation_macros:
                if macro not in existing_macros:
                    existing_macros.append(macro)
        if evaluation.metric_violations:
            result["qa_metric_violations"] = [
                violation.to_dict() for violation in evaluation.metric_violations
            ]
        if evaluation.untracked_metrics:
            untracked = result.setdefault("qa_untracked_metrics", [])
            for metric in evaluation.untracked_metrics:
                if metric not in untracked:
                    untracked.append(metric)
        if evaluation.tests_executed:
            result["qa_tests_executed"] = list(evaluation.tests_executed)
        result["qa_severity_score"] = evaluation.severity
        result["qa_severity_level"] = evaluation.severity_level
        result["qa_evaluation"] = evaluation
        result["qa_evaluation_payload"] = evaluation.to_dict()

        return result

    def required_tests(self) -> Sequence[str]:
        """Return the QA test identifiers that this agent is expected to execute."""

        return self.qa_engine.get_agent_tests(self.name)
