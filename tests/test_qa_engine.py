"""Unit tests for the QAEngine covering rule loading, budget evaluation, and trust management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pytest

from macro_system.engine import MacroEngine
from qa.qa_engine import MacroValidationResult, MetricViolation, QAEngine, QARules


@pytest.fixture()
def qa_files() -> Dict[str, Path]:
    """Provide paths to the QA rules and schema files bundled with the repository."""

    base = Path(__file__).resolve().parent.parent
    return {
        "rules": base / "config" / "qa_rules.json",
        "schema": base / "config" / "qa_rules.schema.json",
    }


@pytest.fixture()
def qa_engine(qa_files: Dict[str, Path]) -> QAEngine:
    """Load QA rules through the schema validator and return a ready engine."""

    rules = QARules.load_from_file(qa_files["rules"], qa_files["schema"])
    return QAEngine(rules)


@pytest.fixture()
def qa_engine_with_source(tmp_path: Path, qa_files: Dict[str, Path]) -> QAEngine:
    """Provide a QAEngine wired to on-disk rule files for refresh testing."""

    rules_copy = tmp_path / "qa_rules.json"
    schema_copy = tmp_path / "qa_rules.schema.json"
    rules_copy.write_text(qa_files["rules"].read_text(encoding="utf-8"), encoding="utf-8")
    schema_copy.write_text(qa_files["schema"].read_text(encoding="utf-8"), encoding="utf-8")

    engine = QAEngine.from_files(rules_copy, schema_copy)
    return engine


def test_get_agent_budget_and_tests(qa_engine: QAEngine) -> None:
    """Ensure agent budgets and test lists are loaded as defined in the rules file."""

    frontend_budget = qa_engine.get_agent_budget("Frontend")
    assert frontend_budget is not None
    assert frontend_budget.budgets["lighthouse_score"] == 90
    assert "lighthouse" in qa_engine.get_agent_tests("Frontend")
    assert qa_engine.get_agent_budget("Unknown") is None


def test_metric_policies_loaded(qa_engine: QAEngine) -> None:
    """Metric policies should expose comparison modes, weights, and macros."""

    frontend_budget = qa_engine.get_agent_budget("Frontend")
    assert frontend_budget is not None
    policy = frontend_budget.get_metric_policy("lighthouse_score")
    assert policy is not None
    assert policy.resolved_comparison() == "gte"
    assert policy.normalised_weight() == pytest.approx(1.3, rel=1e-3)
    assert "::frontendgen-tests" in policy.remediation_macros


def test_validate_macro_definition_detects_missing_fields(qa_engine: QAEngine) -> None:
    """Macro validation should flag missing required fields according to the rules."""

    missing = qa_engine.validate_macro_definition({"inputs": [], "outputs": []})
    assert "failure_cases" in missing
    assert "dependencies" in missing
    assert "context" in missing


def test_assess_macro_definition_success_path(qa_engine: QAEngine) -> None:
    """Macro assessment should recognise valid definitions with allowed contexts."""

    macro = {
        "inputs": ["payload"],
        "outputs": ["artifact"],
        "failure_cases": ["timeout"],
        "dependencies": ["service"],
        "context": ["dev", "staging"],
    }
    result = qa_engine.assess_macro_definition(macro)
    assert isinstance(result, MacroValidationResult)
    assert result.is_valid is True
    assert result.missing_fields == []
    assert result.empty_fields == []
    assert result.invalid_context == []
    assert set(result.recommended_context) == set(qa_engine.get_macro_default_context())


def test_assess_macro_definition_flags_invalid_context(qa_engine: QAEngine) -> None:
    """Macro assessment should detect contexts outside of the allowed defaults."""

    macro = {
        "inputs": ["payload"],
        "outputs": ["artifact"],
        "failure_cases": ["timeout"],
        "dependencies": ["service"],
        "context": ["qa", "prod"],
    }
    result = qa_engine.assess_macro_definition(macro)
    assert result.is_valid is False
    assert result.invalid_context == ["qa"]
    assert any("context" in step for step in result.remediation)


def test_record_agent_failure_updates_trust(qa_engine: QAEngine) -> None:
    """Recording a failure should decay the agent's trust score and retain history."""

    initial_trust = qa_engine.get_agent_trust("Frontend")
    qa_engine.record_agent_failure("Frontend", "Exceeded latency budget")
    assert qa_engine.get_agent_trust("Frontend") < initial_trust
    assert qa_engine.get_failure_history("Frontend") == ["Exceeded latency budget"]


def test_weighted_failures_decay_trust_faster(qa_engine: QAEngine) -> None:
    """Failure weights should amplify trust decay according to severity."""

    initial_trust = qa_engine.get_agent_trust("Frontend")
    qa_engine.record_agent_failures("Frontend", ["major regression"], weights=[2.0])
    expected = max(
        initial_trust * (qa_engine.FAILURE_DECAY**2.0),
        qa_engine.FAILURE_FLOOR,
    )
    assert qa_engine.get_agent_trust("Frontend") == pytest.approx(expected)


def test_record_agent_success_caps_growth(qa_engine: QAEngine) -> None:
    """Successful events should increment trust but stay within the configured ceiling."""

    qa_engine.record_agent_success("Frontend")
    assert qa_engine.get_agent_trust("Frontend") > 1.0
    for _ in range(50):
        qa_engine.record_agent_success("Frontend")
    assert qa_engine.get_agent_trust("Frontend") <= QAEngine.SUCCESS_CEILING


def test_evaluate_metrics_detects_numeric_and_boolean_violations(qa_engine: QAEngine) -> None:
    """Budget evaluation should detect threshold breaches for numeric and boolean metrics."""

    metrics = {"lighthouse_score": 80, "accessibility_pass": False}
    violations = qa_engine.evaluate_metrics("Frontend", metrics)
    assert any("lighthouse_score" in violation for violation in violations)
    assert any("accessibility_pass" in violation for violation in violations)


def test_evaluate_metrics_detailed_returns_structured_data(qa_engine: QAEngine) -> None:
    """Detailed metric evaluation should surface policy metadata and remediation macros."""

    metrics = {"lighthouse_score": 70, "accessibility_pass": True}
    violations = qa_engine.evaluate_metrics_detailed("Frontend", metrics)
    assert any(isinstance(item, MetricViolation) for item in violations)
    lighthouse_violation = next(item for item in violations if item.metric == "lighthouse_score")
    assert lighthouse_violation.weight > 1.0
    assert "::frontendgen-tests" in lighthouse_violation.remediation_macros


def test_assess_task_result_success_returns_evaluation(qa_engine: QAEngine) -> None:
    """Successful assessments should boost trust and return a populated evaluation object."""

    metrics = {"lighthouse_score": 95, "accessibility_pass": True}
    required_tests = qa_engine.get_agent_tests("Frontend")
    evaluation = qa_engine.assess_task_result("Frontend", metrics, tests_executed=required_tests)
    assert evaluation.passed is True
    assert evaluation.violations == []
    assert evaluation.metrics["lighthouse_score"] == 95
    assert evaluation.trust > 1.0
    assert "jest_unit" in evaluation.required_tests
    assert evaluation.missing_tests == []
    assert evaluation.tests_executed == required_tests
    assert evaluation.remediation == []
    assert evaluation.remediation_macros == []
    assert evaluation.metric_violations == []
    assert evaluation.severity == 0.0
    assert evaluation.severity_level == "none"
    assert evaluation.untracked_metrics == []


def test_assess_task_result_failure_includes_remediation(qa_engine: QAEngine) -> None:
    """Failed assessments should return remediation guidance and log history."""

    metrics = {"lighthouse_score": 50, "accessibility_pass": False}
    evaluation = qa_engine.assess_task_result("Frontend", metrics, tests_executed=["jest_unit"])
    assert evaluation.passed is False
    assert len(evaluation.violations) >= 3
    assert evaluation.remediation, "Expected remediation actions when violations occur"
    assert qa_engine.get_failure_history("Frontend")
    assert sorted(evaluation.missing_tests) == sorted(
        set(qa_engine.get_agent_tests("Frontend")) - {"jest_unit"}
    )
    assert evaluation.tests_executed == ["jest_unit"]
    assert any("Required QA tests not executed" in violation for violation in evaluation.violations)
    assert any(isinstance(item, MetricViolation) for item in evaluation.metric_violations)
    assert "::frontendgen-access" in evaluation.remediation_macros
    assert evaluation.severity > 0
    assert evaluation.severity_level in {"medium", "high"}
    assert evaluation.untracked_metrics == []


def test_generate_remediation_plan_scales_with_history(qa_engine: QAEngine) -> None:
    """Repeated failures should trigger escalation guidance in the remediation plan."""

    qa_engine.record_agent_failure("Frontend", "latency regression")
    qa_engine.record_agent_failure("Frontend", "latency regression")
    qa_engine.record_agent_failure("Frontend", "latency regression")
    plan = qa_engine.generate_remediation_plan("Frontend")
    assert any("Escalate" in step for step in plan.steps)
    assert any("Profile performance" in step for step in plan.steps)


def test_generate_remediation_plan_includes_macros(qa_engine: QAEngine) -> None:
    """Metric-specific remediation should include macro recommendations."""

    plan = qa_engine.generate_remediation_plan("Frontend", violated_metrics=["lighthouse_score"])
    assert any("Optimise" in step for step in plan.steps)
    assert "::frontendgen-motion" in plan.macros


def test_assess_task_result_reports_untracked_metrics(qa_engine: QAEngine) -> None:
    """Assessments should surface metrics that are not yet governed by QA budgets."""

    metrics = {
        "lighthouse_score": 95,
        "accessibility_pass": True,
        "runtime_ms": 120,
    }
    evaluation = qa_engine.assess_task_result(
        "Frontend", metrics, tests_executed=qa_engine.get_agent_tests("Frontend")
    )
    assert evaluation.passed is True
    assert evaluation.untracked_metrics == ["runtime_ms"]
    assert any("untracked" in step.lower() for step in evaluation.remediation)
    assert evaluation.severity == 0.0
    assert evaluation.severity_level == "none"


def test_evaluate_metrics_missing_metric_is_flagged(qa_engine: QAEngine) -> None:
    """Budget evaluation must flag when required metrics are absent from the task result."""

    metrics = {"accessibility_pass": True}
    violations = qa_engine.evaluate_metrics("Frontend", metrics)
    assert any("missing" in violation for violation in violations)


def test_assess_task_result_requires_all_tests(qa_engine: QAEngine) -> None:
    """Agents must report all mandatory tests; omissions should produce violations."""

    metrics = {"lighthouse_score": 95, "accessibility_pass": True}
    evaluation = qa_engine.assess_task_result("Frontend", metrics, tests_executed=["lighthouse"])
    assert evaluation.passed is False
    assert any("Required QA tests not executed" in violation for violation in evaluation.violations)
    assert sorted(evaluation.missing_tests) == sorted(
        set(qa_engine.get_agent_tests("Frontend")) - {"lighthouse"}
    )


def test_assess_exception_records_failure(qa_engine: QAEngine) -> None:
    """Exceptions during task execution should record failures and remediation guidance."""

    initial_trust = qa_engine.get_agent_trust("Frontend")
    evaluation = qa_engine.assess_exception("Frontend", RuntimeError("boom"))

    assert evaluation.passed is False
    assert evaluation.error == {"type": "RuntimeError", "message": "boom"}
    assert qa_engine.get_agent_trust("Frontend") < initial_trust
    assert set(evaluation.missing_tests) == set(qa_engine.get_agent_tests("Frontend"))
    assert any("QA tests" in step for step in evaluation.remediation)
    assert "::frontendgen-access" in evaluation.remediation_macros
    assert evaluation.severity >= 1.0
    assert evaluation.severity_level in {"medium", "high"}
    assert evaluation.tests_executed == []


def test_generate_health_report_includes_agents(qa_engine: QAEngine) -> None:
    """Health report should expose trust metrics and budgets for each agent."""

    report = qa_engine.generate_health_report()
    assert report["rules_version"] == "1.0.0"
    assert "Frontend" in report["agents"]
    frontend = report["agents"]["Frontend"]
    assert "trust" in frontend
    assert "budgets" in frontend
    assert "metrics" in frontend
    assert frontend["metrics"]["lighthouse_score"]["comparison"] == "gte"
    assert "::frontendgen-tests" in frontend["recommended_macros"]


def test_reload_rules_reconciles_agents(
    qa_engine: QAEngine, tmp_path: Path, qa_files: Dict[str, Path]
) -> None:
    """Reloading rules should adjust tracked agents and reset trust for new ones."""

    rules_data = json.loads(qa_files["rules"].read_text(encoding="utf-8"))
    rules_data["agents"]["Data"] = {"budgets": {"throughput": 1000}, "tests": ["load_test"]}
    new_rules_path = tmp_path / "qa_rules.json"
    new_rules_path.write_text(json.dumps(rules_data), encoding="utf-8")

    new_rules = QARules.load_from_file(new_rules_path, qa_files["schema"])
    result = qa_engine.reload_rules(new_rules)

    assert "Data" in qa_engine.rules.agents
    assert qa_engine.get_agent_trust("Data") == 1.0
    assert result["added_agents"] == ["Data"]


def test_refresh_from_source_updates_version(qa_engine_with_source: QAEngine) -> None:
    """Refreshing from source should reload modified rule files and surface changes."""

    assert qa_engine_with_source.rules_source is not None
    rules_path, _ = qa_engine_with_source.rules_source
    rules_data = json.loads(rules_path.read_text(encoding="utf-8"))
    rules_data["version"] = "1.1.0"
    rules_path.write_text(json.dumps(rules_data), encoding="utf-8")

    changes = qa_engine_with_source.refresh_from_source()
    assert qa_engine_with_source.rules.version == "1.1.0"
    assert changes == {"added_agents": [], "removed_agents": []}


def test_list_all_remediation_macros_exposes_union(qa_engine: QAEngine) -> None:
    """The engine should return the union of remediation macros across all agents."""

    macros = qa_engine.list_all_remediation_macros()
    assert "::frontendgen-access" in macros
    assert "::perfprofile" in macros


def test_audit_macro_catalog_detects_missing_macros(qa_engine: QAEngine) -> None:
    """Macro catalog audits should flag missing remediation macros per agent."""

    base = Path(__file__).resolve().parent.parent
    macros_path = base / "macro_system" / "macros.json"
    engine = MacroEngine.from_json(macros_path)
    available = engine.available_macros()

    full_audit = qa_engine.audit_macro_catalog(available)
    assert full_audit["missing"] == {}
    assert full_audit["missing_macros"] == []
    assert "::frontendgen" in full_audit["unused_available"]

    limited_audit = qa_engine.audit_macro_catalog(
        [macro for macro in available if macro != "::frontendgen-access"]
    )
    assert limited_audit["missing"]["Frontend"] == ["::frontendgen-access"]
    assert "::frontendgen-access" in limited_audit["missing_macros"]
