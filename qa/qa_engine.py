"""
SECTION: Header & Purpose
    - Implements QARules data container and QAEngine runtime facade for QA governance.
    - Exposes utilities for loading machine-readable QA rules, querying agent budgets, validating macros,
      enforcing mandatory test execution, tracking agent trust metrics, scoring severity, detecting untracked
      metrics, auditing remediation macros, and refreshing QA rules at runtime.

SECTION: Imports / Dependencies
    - Relies only on the Python standard library for portability (json, pathlib, dataclasses, typing, logging).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Sequence, Set, Tuple, Literal, cast


class QARulesError(Exception):
    """Exception raised when QA rules cannot be loaded or validated."""


@dataclass
class MetricPolicy:
    """Optional metadata describing how to evaluate and remediate an agent metric."""

    comparison: Literal["auto", "lte", "gte", "eq"] = "auto"
    remediation_steps: List[str] = field(default_factory=list)
    remediation_macros: List[str] = field(default_factory=list)
    weight: float = 1.0

    def resolved_comparison(self) -> Literal["auto", "lte", "gte", "eq"]:
        """Return the configured comparison mode for the metric."""

        return self.comparison

    def normalised_weight(self) -> float:
        """Return the non-negative weight multiplier associated with this metric."""

        return max(self.weight, 0.0)


@dataclass
class MetricViolation:
    """Structured description of a metric violation detected during assessment."""

    metric: str
    message: str
    weight: float = 1.0
    remediation_steps: List[str] = field(default_factory=list)
    remediation_macros: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the violation for downstream event consumers."""

        return {
            "metric": self.metric,
            "message": self.message,
            "weight": self.weight,
            "remediation_steps": list(self.remediation_steps),
            "remediation_macros": list(self.remediation_macros),
        }


@dataclass
class RemediationPlan:
    """Collection of remediation steps and remediation macros for a failure."""

    steps: List[str] = field(default_factory=list)
    macros: List[str] = field(default_factory=list)


@dataclass
class AgentBudget:
    """Container describing the QA budget thresholds and required tests for an agent."""

    budgets: Dict[str, Any] = field(default_factory=dict)
    tests: List[str] = field(default_factory=list)
    metric_policies: Dict[str, MetricPolicy] = field(default_factory=dict)

    def get_metric_names(self) -> Iterable[str]:
        """Return the collection of metric keys defined for the agent."""

        return self.budgets.keys()

    def get_metric_policy(self, metric_name: str) -> Optional[MetricPolicy]:
        """Return the configured metric policy for ``metric_name`` if present."""

        return self.metric_policies.get(metric_name)


@dataclass
class QAEvaluation:
    """Structured result describing the outcome of assessing an agent task."""

    agent: str
    passed: bool
    metrics: Dict[str, Any] = field(default_factory=dict)
    violations: List[str] = field(default_factory=list)
    trust: float = 0.0
    failure_history: List[str] = field(default_factory=list)
    remediation: List[str] = field(default_factory=list)
    required_tests: List[str] = field(default_factory=list)
    missing_tests: List[str] = field(default_factory=list)
    tests_executed: List[str] = field(default_factory=list)
    remediation_macros: List[str] = field(default_factory=list)
    metric_violations: List[MetricViolation] = field(default_factory=list)
    severity: float = 0.0
    severity_level: str = "none"
    untracked_metrics: List[str] = field(default_factory=list)
    error: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the evaluation as a JSON-friendly dictionary for cross-language consumers."""

        payload = {
            "agent": self.agent,
            "status": "success" if self.passed else "failure",
            "passed": self.passed,
            "metrics": dict(self.metrics),
            "violations": list(self.violations),
            "trust": self.trust,
            "failure_history": list(self.failure_history),
            "remediation": list(self.remediation),
            "required_tests": list(self.required_tests),
            "missing_tests": list(self.missing_tests),
            "tests_executed": list(self.tests_executed),
            "remediation_macros": list(self.remediation_macros),
            "metric_violations": [violation.to_dict() for violation in self.metric_violations],
            "severity": self.severity,
            "severity_level": self.severity_level,
            "untracked_metrics": list(self.untracked_metrics),
            "error": dict(self.error) if self.error else None,
        }
        return payload

    def to_event_payload(self) -> Dict[str, Any]:
        """Serialize the evaluation for emission on the QA event bus."""

        return self.to_dict()


@dataclass
class MacroValidationResult:
    """Detailed evaluation describing the validity of a macro definition."""

    macro: Dict[str, Any]
    is_valid: bool
    missing_fields: List[str] = field(default_factory=list)
    empty_fields: List[str] = field(default_factory=list)
    invalid_context: List[str] = field(default_factory=list)
    recommended_context: List[str] = field(default_factory=list)
    remediation: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the validation result for cross-language consumption."""

        return {
            "is_valid": self.is_valid,
            "missing_fields": list(self.missing_fields),
            "empty_fields": list(self.empty_fields),
            "invalid_context": list(self.invalid_context),
            "recommended_context": list(self.recommended_context),
            "remediation": list(self.remediation),
        }


@dataclass
class QARules:
    """Immutable snapshot of QA rules loaded from disk."""

    version: str
    agents: Dict[str, AgentBudget] = field(default_factory=dict)
    macros: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def load_from_file(rules_path: Path, schema_path: Optional[Path] = None) -> "QARules":
        """Load QA rules from ``rules_path`` and validate the payload against ``schema_path`` if provided."""

        try:
            data = json.loads(rules_path.read_text(encoding="utf-8"))
        except OSError as exc:  # file IO issues
            raise QARulesError(f"Failed to read QA rules file: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise QARulesError(f"QA rules file is not valid JSON: {exc}") from exc

        if schema_path is not None:
            try:
                schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
            except OSError as exc:
                raise QARulesError(f"Failed to read QA schema file: {exc}") from exc
            except json.JSONDecodeError as exc:
                raise QARulesError(f"QA schema file is not valid JSON: {exc}") from exc
            _validate_against_embedded_schema(data, schema_data)

        agents: Dict[str, AgentBudget] = {}
        for agent_name, config in data.get("agents", {}).items():
            agents[agent_name] = AgentBudget(
                budgets=dict(config.get("budgets", {})),
                tests=list(config.get("tests", [])),
                metric_policies=_parse_metric_policies(agent_name, config.get("metrics")),
            )

        macros = dict(data.get("macros", {}))
        return QARules(version=str(data.get("version", "0.0.0")), agents=agents, macros=macros)


def _validate_against_embedded_schema(data: MutableMapping[str, Any], schema: MutableMapping[str, Any]) -> None:
    """Perform a focused validation that mirrors the bundled schema requirements."""

    def _expect(condition: bool, message: str) -> None:
        if not condition:
            raise QARulesError(f"QA rules validation failed: {message}")

    _expect(isinstance(data, dict), "top-level structure must be an object")

    properties = schema.get("properties", {})
    required_keys = tuple(schema.get("required", ("version", "agents", "macros")))
    for required_key in required_keys:
        _expect(required_key in data, f"missing required property '{required_key}'")

    allowed_top_level = set(properties.keys()) or set(required_keys)
    extra_top_level = set(data) - allowed_top_level
    _expect(not extra_top_level, f"unknown top-level keys: {sorted(extra_top_level)}")

    _expect(isinstance(data["version"], str), "'version' must be a string")

    agents = data["agents"]
    _expect(isinstance(agents, dict), "'agents' must be an object")
    agent_properties = (
        schema.get("properties", {})
        .get("agents", {})
        .get("additionalProperties", {})
        .get("properties", {})
    )
    allowed_agent_keys = set(agent_properties.keys()) or {"budgets", "tests"}

    for agent_name, agent_cfg in agents.items():
        _expect(isinstance(agent_cfg, dict), f"agent '{agent_name}' configuration must be an object")
        extra_keys = set(agent_cfg) - allowed_agent_keys
        _expect(not extra_keys, f"agent '{agent_name}' has unknown keys: {sorted(extra_keys)}")
        _expect("budgets" in agent_cfg, f"agent '{agent_name}' missing 'budgets'")
        _expect("tests" in agent_cfg, f"agent '{agent_name}' missing 'tests'")

        budgets = agent_cfg["budgets"]
        _expect(isinstance(budgets, dict), f"agent '{agent_name}' budgets must be an object")
        _expect(not isinstance(budgets, bool), f"agent '{agent_name}' budgets must not be boolean")
        for metric_name, metric_value in budgets.items():
            _expect(
                isinstance(metric_value, (int, float, bool, str)),
                f"agent '{agent_name}' budget '{metric_name}' must be number, boolean, or string",
            )

        tests = agent_cfg["tests"]
        _expect(isinstance(tests, list), f"agent '{agent_name}' tests must be an array")
        _expect(all(isinstance(test_name, str) for test_name in tests), f"agent '{agent_name}' test entries must be strings")
        for test_name in tests:
            _expect(isinstance(test_name, str), f"agent '{agent_name}' test entries must be strings")

        metrics_cfg = agent_cfg.get("metrics")
        if metrics_cfg is not None:
            _expect(isinstance(metrics_cfg, dict), f"agent '{agent_name}' metrics must be an object")
            for metric_name, policy_cfg in metrics_cfg.items():
                _expect(isinstance(metric_name, str), "metric keys must be strings")
                _expect(isinstance(policy_cfg, dict), f"agent '{agent_name}' metric '{metric_name}' policy must be an object")
                comparison = policy_cfg.get("comparison", "auto")
                _expect(
                    comparison in {"auto", "lte", "gte", "eq"},
                    f"agent '{agent_name}' metric '{metric_name}' comparison must be one of 'auto', 'lte', 'gte', 'eq'",
                )
                remediation_steps = policy_cfg.get("remediation_steps")
                if remediation_steps is not None:
                    _expect(
                        isinstance(remediation_steps, list)
                        and all(isinstance(step, str) for step in remediation_steps),
                        f"agent '{agent_name}' metric '{metric_name}' remediation_steps must be an array of strings",
                    )
                remediation_macros = policy_cfg.get("remediation_macros")
                if remediation_macros is not None:
                    _expect(
                        isinstance(remediation_macros, list)
                        and all(isinstance(entry, str) for entry in remediation_macros),
                        f"agent '{agent_name}' metric '{metric_name}' remediation_macros must be an array of strings",
                    )
                if "weight" in policy_cfg:
                    weight = policy_cfg["weight"]
                    _expect(
                        isinstance(weight, (int, float)) and weight >= 0,
                        f"agent '{agent_name}' metric '{metric_name}' weight must be a non-negative number",
                    )

    macros = data["macros"]
    _expect(isinstance(macros, dict), "'macros' must be an object")
    macro_properties = schema.get("properties", {}).get("macros", {}).get("properties", {})
    allowed_macro_keys = set(macro_properties.keys()) or {"required_fields", "default_context"}
    extra_macro_keys = set(macros) - allowed_macro_keys
    _expect(not extra_macro_keys, f"macros object has unknown keys: {sorted(extra_macro_keys)}")
    _expect("required_fields" in macros, "macros missing 'required_fields'")
    _expect("default_context" in macros, "macros missing 'default_context'")

    required_fields = macros["required_fields"]
    _expect(isinstance(required_fields, list), "'required_fields' must be an array")
    for field_name in required_fields:
        _expect(isinstance(field_name, str), "each required field must be a string")

    default_context = macros["default_context"]
    _expect(isinstance(default_context, list), "'default_context' must be an array")
    for ctx in default_context:
        _expect(isinstance(ctx, str), "each default context entry must be a string")
    _expect(len(set(default_context)) == len(default_context), "'default_context' entries must be unique")


def _coerce_string_list(value: Any, error_context: str) -> List[str]:
    """Return a list of unique strings, raising when ``value`` is not a list of strings."""

    if value is None:
        return []
    if not isinstance(value, list):
        raise QARulesError(f"{error_context} must be defined as an array of strings")

    result: List[str] = []
    seen: Set[str] = set()
    for entry in value:
        if not isinstance(entry, str):
            raise QARulesError(f"{error_context} entries must be strings")
        if entry not in seen:
            seen.add(entry)
            result.append(entry)
    return result


def _parse_metric_policies(agent_name: str, raw: Any) -> Dict[str, MetricPolicy]:
    """Parse the optional metric policy configuration for ``agent_name``."""

    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise QARulesError(
            f"Metrics configuration for agent '{agent_name}' must be an object when provided"
        )

    policies: Dict[str, MetricPolicy] = {}
    for metric_name, payload in raw.items():
        if not isinstance(metric_name, str):
            raise QARulesError("Metric names must be strings")
        if not isinstance(payload, dict):
            raise QARulesError(
                f"Metric policy for agent '{agent_name}' metric '{metric_name}' must be an object"
            )

        comparison = str(payload.get("comparison", "auto")).lower()
        if comparison not in {"auto", "lte", "gte", "eq"}:
            raise QARulesError(
                f"Metric policy comparison for agent '{agent_name}' metric '{metric_name}' must be one of 'auto', 'lte', 'gte', 'eq'"
            )

        remediation_steps = _coerce_string_list(
            payload.get("remediation_steps"),
            f"agent '{agent_name}' metric '{metric_name}' remediation_steps",
        )
        remediation_macros = _coerce_string_list(
            payload.get("remediation_macros"),
            f"agent '{agent_name}' metric '{metric_name}' remediation_macros",
        )

        raw_weight = payload.get("weight", 1.0)
        try:
            weight = float(raw_weight)
        except (TypeError, ValueError) as exc:
            raise QARulesError(
                f"Metric policy weight for agent '{agent_name}' metric '{metric_name}' must be numeric"
            ) from exc
        if weight < 0:
            raise QARulesError(
                f"Metric policy weight for agent '{agent_name}' metric '{metric_name}' must be non-negative"
            )

        policies[metric_name] = MetricPolicy(
            comparison=cast(Literal["auto", "lte", "gte", "eq"], comparison),
            remediation_steps=remediation_steps,
            remediation_macros=remediation_macros,
            weight=weight,
        )

    return policies


class QAEngine:
    """Runtime QA coordinator that provides budget queries, macro validation, and trust tracking."""

    FAILURE_DECAY: float = 0.9
    FAILURE_FLOOR: float = 0.1
    SUCCESS_BOOST: float = 0.05
    SUCCESS_CEILING: float = 1.5
    NUMERIC_UPPER_BOUND_HINTS: tuple[str, ...] = ("latency", "duration", "time", "error", "p95", "p99")

    def __init__(
        self,
        rules: QARules,
        *,
        rules_source: Optional[Tuple[Path, Optional[Path]]] = None,
    ) -> None:
        self.rules = rules
        self.trust_scores: Dict[str, float] = {agent: 1.0 for agent in rules.agents}
        self.agent_failures: Dict[str, List[str]] = {agent: [] for agent in rules.agents}
        self._rules_source: Optional[Tuple[Path, Optional[Path]]] = rules_source
        logging.debug("QAEngine initialised with agents: %s", list(self.rules.agents.keys()))

    @classmethod
    def from_files(cls, rules_path: Path, schema_path: Optional[Path] = None) -> "QAEngine":
        """Factory helper that loads rules from disk and returns a ready-to-use engine instance."""

        rules = QARules.load_from_file(rules_path, schema_path)
        return cls(rules, rules_source=(rules_path, schema_path))

    @property
    def rules_source(self) -> Optional[Tuple[Path, Optional[Path]]]:
        """Return the configured rules source paths, if the engine was built from files."""

        return self._rules_source

    def attach_rules_source(
        self, rules_path: Path, schema_path: Optional[Path] = None
    ) -> None:
        """Associate on-disk rule locations for future refresh operations."""

        self._rules_source = (rules_path, schema_path)

    def get_agent_budget(self, agent_name: str) -> Optional[AgentBudget]:
        """Return the ``AgentBudget`` for ``agent_name`` if one exists."""

        return self.rules.agents.get(agent_name)

    def get_agent_tests(self, agent_name: str) -> List[str]:
        """Return the list of tests that the agent is expected to run."""

        budget = self.get_agent_budget(agent_name)
        return [] if budget is None else list(budget.tests)

    def get_macro_required_fields(self) -> List[str]:
        """Expose the required fields that macro definitions must contain."""

        fields = self.rules.macros.get("required_fields", [])
        return list(fields) if isinstance(fields, list) else []

    def get_macro_default_context(self) -> List[str]:
        """Return the default macro context list used by orchestrators."""

        context = self.rules.macros.get("default_context", [])
        return list(context) if isinstance(context, list) else []

    @staticmethod
    def _categorise_severity(score: float) -> str:
        """Return a human-readable severity label for the provided ``score``."""

        if score <= 0:
            return "none"
        if score < 1.0:
            return "low"
        if score < 2.0:
            return "medium"
        return "high"

    def validate_macro_definition(self, macro_def: Dict[str, Any]) -> List[str]:
        """Validate ``macro_def`` and return a list of missing required fields."""

        return self.assess_macro_definition(macro_def).missing_fields

    def assess_macro_definition(self, macro_def: Dict[str, Any]) -> MacroValidationResult:
        """Return a comprehensive validation result for the provided macro definition."""

        missing: List[str] = []
        empty: List[str] = []
        invalid_context: List[str] = []
        required_fields = self.get_macro_required_fields()
        default_context = self.get_macro_default_context()

        for field_name in required_fields:
            if field_name not in macro_def:
                missing.append(field_name)
                continue

            value = macro_def[field_name]
            if value in (None, "", [], {}):
                empty.append(field_name)

        if "context" in macro_def and "context" not in missing:
            raw_context = macro_def.get("context")
            if isinstance(raw_context, str):
                context_values = [raw_context]
            elif isinstance(raw_context, (list, tuple, set)):
                context_values = [str(entry) for entry in raw_context]
            else:
                invalid_context = ["context"]
                context_values = []

            if not invalid_context:
                allowed = set(default_context)
                invalid_context = [value for value in context_values if value not in allowed]

        remediation: List[str] = []
        if missing:
            remediation.append(
                "Populate required macro fields: " + ", ".join(sorted(missing))
            )
        if empty:
            remediation.append(
                "Ensure required fields are not empty: " + ", ".join(sorted(empty))
            )
        if invalid_context:
            remediation.append(
                "Align macro context with allowed values: " + ", ".join(sorted(default_context))
            )

        is_valid = not (missing or empty or invalid_context)
        return MacroValidationResult(
            macro=dict(macro_def),
            is_valid=is_valid,
            missing_fields=missing,
            empty_fields=empty,
            invalid_context=invalid_context,
            recommended_context=default_context,
            remediation=remediation,
        )

    def reload_rules(self, rules: QARules) -> Dict[str, List[str]]:
        """Replace the in-memory rules snapshot and reconcile trust tracking state."""

        previous_agents = set(self.rules.agents)
        next_agents = set(rules.agents)

        added = sorted(next_agents - previous_agents)
        removed = sorted(previous_agents - next_agents)

        self.rules = rules

        for agent in added:
            self.trust_scores[agent] = 1.0
            self.agent_failures[agent] = []

        for agent in removed:
            self.trust_scores.pop(agent, None)
            self.agent_failures.pop(agent, None)

        logging.info(
            "QAEngine rules reloaded: added agents=%s removed agents=%s",
            added,
            removed,
        )

        return {"added_agents": added, "removed_agents": removed}

    def refresh_from_source(self) -> Dict[str, List[str]]:
        """Reload QA rules from the configured on-disk source, if available."""

        if self._rules_source is None:
            raise QARulesError("No rules source configured for refresh")

        rules_path, schema_path = self._rules_source
        refreshed = QARules.load_from_file(rules_path, schema_path)
        return self.reload_rules(refreshed)

    def assess_task_result(
        self,
        agent_name: str,
        metrics: Dict[str, Any],
        tests_executed: Optional[Sequence[str]] = None,
    ) -> QAEvaluation:
        """Evaluate ``metrics`` and executed tests, then return a structured assessment."""

        executed_tests = [str(test) for test in tests_executed] if tests_executed else []
        metric_violations = self.evaluate_metrics_detailed(agent_name, metrics)
        missing_tests = self.evaluate_required_tests(agent_name, executed_tests)

        violation_messages = [violation.message for violation in metric_violations]
        violation_weights = [violation.weight for violation in metric_violations]
        violated_metrics = [violation.metric for violation in metric_violations]

        if missing_tests:
            violation_messages.append(
                "Required QA tests not executed: " + ", ".join(sorted(missing_tests))
            )
            violation_weights.append(1.0)

        severity_score = float(sum(violation_weights)) if violation_weights else 0.0
        severity_level = self._categorise_severity(severity_score)
        untracked_metrics = self.identify_untracked_metrics(agent_name, metrics)

        if violation_messages:
            self.record_agent_failures(
                agent_name,
                violation_messages,
                weights=violation_weights,
            )
            remediation_plan = self.generate_remediation_plan(
                agent_name,
                violated_metrics=violated_metrics,
                missing_tests=missing_tests,
            )
        else:
            self.record_agent_success(agent_name, "QA metrics within budget")
            remediation_plan = RemediationPlan()

        remediation_steps = list(remediation_plan.steps)
        if untracked_metrics:
            remediation_steps.append(
                "Register QA budgets for untracked metrics: "
                + ", ".join(untracked_metrics)
            )

        evaluation = QAEvaluation(
            agent=agent_name,
            passed=not violation_messages,
            metrics=dict(metrics),
            violations=list(violation_messages),
            trust=self.get_agent_trust(agent_name),
            failure_history=self.get_failure_history(agent_name),
            remediation=_deduplicate_preserve_order(remediation_steps),
            required_tests=self.get_agent_tests(agent_name),
            missing_tests=list(missing_tests),
            tests_executed=executed_tests,
            remediation_macros=list(remediation_plan.macros),
            metric_violations=list(metric_violations),
            severity=severity_score,
            severity_level=severity_level,
            untracked_metrics=untracked_metrics,
            error=None,
        )
        return evaluation

    def record_agent_failures(
        self, agent_name: str, reasons: Sequence[str], *, weights: Optional[Sequence[float]] = None
    ) -> None:
        """Record one or more QA failures while applying weighted trust decay per reason."""

        if not reasons:
            return

        failures = self.agent_failures.setdefault(agent_name, [])
        weight_list = list(weights) if weights is not None else []

        for index, reason in enumerate(reasons):
            failures.append(reason)
            raw_weight = weight_list[index] if index < len(weight_list) else 1.0
            try:
                weight = float(raw_weight)
            except (TypeError, ValueError):
                weight = 1.0
            weight = max(weight, 0.0)
            decay_factor = self.FAILURE_DECAY ** weight if weight > 0 else 1.0

            current_score = self.trust_scores.get(agent_name, 1.0)
            updated_score = max(current_score * decay_factor, self.FAILURE_FLOOR)
            self.trust_scores[agent_name] = updated_score
            logging.warning("QA failure recorded for agent '%s': %s", agent_name, reason)

    def record_agent_failure(self, agent_name: str, reason: str) -> None:
        """Compatibility wrapper that records a single QA failure reason."""

        self.record_agent_failures(agent_name, [reason], weights=[1.0])

    def record_agent_success(self, agent_name: str, note: str | None = None) -> None:
        """Increase trust following a successful QA outcome to encourage recovery over time."""

        current_score = self.trust_scores.get(agent_name, 1.0)
        updated_score = min(current_score + self.SUCCESS_BOOST, self.SUCCESS_CEILING)
        self.trust_scores[agent_name] = updated_score
        if note:
            logging.info("QA success recorded for agent '%s': %s", agent_name, note)

    def get_agent_trust(self, agent_name: str) -> float:
        """Return the trust score for ``agent_name`` (defaults to ``0.0`` for unknown agents)."""

        return self.trust_scores.get(agent_name, 0.0)

    def get_failure_history(self, agent_name: str) -> List[str]:
        """Return the list of QA failure reasons that have been recorded for the agent."""

        return list(self.agent_failures.get(agent_name, []))

    def evaluate_metrics_detailed(
        self, agent_name: str, metrics: Dict[str, Any]
    ) -> List[MetricViolation]:
        """Compare ``metrics`` against budgets and return structured violation details."""

        budget = self.get_agent_budget(agent_name)
        if budget is None:
            return []

        violations: List[MetricViolation] = []
        for metric_name, threshold in budget.budgets.items():
            policy = budget.get_metric_policy(metric_name)
            weight = policy.normalised_weight() if policy else 1.0
            remediation_steps = list(policy.remediation_steps) if policy else []
            remediation_macros = list(policy.remediation_macros) if policy else []

            if metric_name not in metrics:
                violations.append(
                    MetricViolation(
                        metric=metric_name,
                        message=f"Metric '{metric_name}' is required by budget but missing from task result",
                        weight=weight,
                        remediation_steps=remediation_steps,
                        remediation_macros=remediation_macros,
                    )
                )
                continue

            value = metrics[metric_name]
            comparison_mode = policy.resolved_comparison() if policy else "auto"

            if isinstance(threshold, (int, float)):
                if value is None or not isinstance(value, (int, float)):
                    violations.append(
                        MetricViolation(
                            metric=metric_name,
                            message=f"Metric '{metric_name}' missing numeric value for comparison",
                            weight=weight,
                            remediation_steps=remediation_steps,
                            remediation_macros=remediation_macros,
                        )
                    )
                    continue

                mode = comparison_mode
                if mode == "auto":
                    mode = "lte" if self._treat_as_upper_bound(metric_name) else "gte"

                if mode == "lte" and value > threshold:
                    violations.append(
                        MetricViolation(
                            metric=metric_name,
                            message=f"Metric '{metric_name}' value {value} exceeds threshold {threshold}",
                            weight=weight,
                            remediation_steps=remediation_steps,
                            remediation_macros=remediation_macros,
                        )
                    )
                elif mode == "gte" and value < threshold:
                    violations.append(
                        MetricViolation(
                            metric=metric_name,
                            message=f"Metric '{metric_name}' value {value} is below minimum {threshold}",
                            weight=weight,
                            remediation_steps=remediation_steps,
                            remediation_macros=remediation_macros,
                        )
                    )
                elif mode == "eq" and value != threshold:
                    violations.append(
                        MetricViolation(
                            metric=metric_name,
                            message=f"Metric '{metric_name}' expected value {threshold} but received {value}",
                            weight=weight,
                            remediation_steps=remediation_steps,
                            remediation_macros=remediation_macros,
                        )
                    )
            elif isinstance(threshold, bool):
                expected = bool(threshold)
                if bool(value) != expected:
                    violations.append(
                        MetricViolation(
                            metric=metric_name,
                            message=f"Metric '{metric_name}' expected boolean {expected} but received {value}",
                            weight=weight,
                            remediation_steps=remediation_steps,
                            remediation_macros=remediation_macros,
                        )
                    )
            else:
                if str(value) != str(threshold):
                    violations.append(
                        MetricViolation(
                            metric=metric_name,
                            message=f"Metric '{metric_name}' expected '{threshold}' but received '{value}'",
                            weight=weight,
                            remediation_steps=remediation_steps,
                            remediation_macros=remediation_macros,
                        )
                    )

        return violations

    def evaluate_metrics(self, agent_name: str, metrics: Dict[str, Any]) -> List[str]:
        """Return violation messages for compatibility with legacy integrations."""

        return [violation.message for violation in self.evaluate_metrics_detailed(agent_name, metrics)]

    @classmethod
    def _treat_as_upper_bound(cls, metric_name: str) -> bool:
        """Infer whether the metric should be evaluated as an upper bound based on its name."""

        name = metric_name.lower()
        return any(hint in name for hint in cls.NUMERIC_UPPER_BOUND_HINTS)

    def generate_remediation_plan(
        self,
        agent_name: str,
        violated_metrics: Optional[Sequence[str]] = None,
        missing_tests: Optional[Sequence[str]] = None,
    ) -> RemediationPlan:
        """Return heuristic remediation actions and recommended macros for an agent."""

        history = self.agent_failures.get(agent_name, [])
        steps: List[str] = []
        macros: List[str] = []

        if missing_tests:
            steps.append(
                "Execute missing QA tests: " + ", ".join(sorted(set(missing_tests)))
            )
        else:
            required_tests = self.get_agent_tests(agent_name)
            if required_tests:
                steps.append(
                    "Re-run mandatory QA tests: " + ", ".join(sorted(required_tests))
                )

        budget = self.get_agent_budget(agent_name)
        if budget is not None and violated_metrics:
            for metric_name in violated_metrics:
                policy = budget.get_metric_policy(metric_name)
                if policy is None:
                    continue
                steps.extend(policy.remediation_steps)
                macros.extend(policy.remediation_macros)

        if len(history) >= 3:
            steps.append(
                "Escalate to Architecture for systemic review due to repeated failures."
            )

        if any("latency" in reason.lower() for reason in history):
            steps.append("Profile performance hotspots and review caching strategies.")

        if not steps:
            steps.append("Review recent changes and update QA rules if necessary.")

        deduped_steps = _deduplicate_preserve_order(steps)
        deduped_macros = _deduplicate_preserve_order(macros)
        return RemediationPlan(steps=deduped_steps, macros=deduped_macros)

    def list_agent_remediation_macros(self, agent_name: str) -> List[str]:
        """Return the set of macros referenced by metric policies for an agent."""

        budget = self.get_agent_budget(agent_name)
        if budget is None:
            return []

        macros: List[str] = []
        for policy in budget.metric_policies.values():
            macros.extend(policy.remediation_macros)
        return _deduplicate_preserve_order(macros)

    def evaluate_required_tests(
        self, agent_name: str, tests_executed: Optional[Sequence[str]]
    ) -> List[str]:
        """Determine which mandatory QA tests were not executed for ``agent_name``."""

        required = self.get_agent_tests(agent_name)
        if not required:
            return []

        if tests_executed is None:
            return list(required)

        executed = {test for test in tests_executed if isinstance(test, str)}
        return [test for test in required if test not in executed]

    def identify_untracked_metrics(self, agent_name: str, metrics: Dict[str, Any]) -> List[str]:
        """Return metrics reported by the agent that are not governed by the QA budget."""

        budget = self.get_agent_budget(agent_name)
        if budget is None:
            return []

        governed = set(budget.budgets.keys())
        unexpected: List[str] = []
        for key, value in metrics.items():
            if key in governed:
                continue
            if key == "tests_executed" or key.startswith("qa_"):
                continue
            if isinstance(value, (dict, list, tuple, set)):
                continue
            unexpected.append(key)
        return _deduplicate_preserve_order(unexpected)

    def assess_exception(self, agent_name: str, error: BaseException) -> QAEvaluation:
        """Generate a failure evaluation for exceptions raised during task execution."""

        message = f"Task execution raised {error.__class__.__name__}: {error}"
        self.record_agent_failure(agent_name, message)
        required_tests = self.get_agent_tests(agent_name)
        plan = self.generate_remediation_plan(agent_name, missing_tests=required_tests)
        remediation = [
            "Inspect stack trace and logs for the raised exception.",
            "Address the root cause and re-run missing QA tests.",
            *plan.steps,
        ]
        remediation_steps = _deduplicate_preserve_order(remediation)
        remediation_macros = plan.macros or self.list_agent_remediation_macros(agent_name)

        severity_score = 1.0
        if required_tests:
            severity_score = max(severity_score, float(len(required_tests)))

        evaluation = QAEvaluation(
            agent=agent_name,
            passed=False,
            metrics={},
            violations=[message],
            trust=self.get_agent_trust(agent_name),
            failure_history=self.get_failure_history(agent_name),
            remediation=remediation_steps,
            required_tests=required_tests,
            missing_tests=list(required_tests),
            tests_executed=[],
            remediation_macros=remediation_macros,
            metric_violations=[],
            severity=severity_score,
            severity_level=self._categorise_severity(severity_score),
            untracked_metrics=[],
            error={
                "type": error.__class__.__name__,
                "message": str(error),
            },
        )
        return evaluation

    def list_all_remediation_macros(self) -> List[str]:
        """Return the union of remediation macros referenced across all agents."""

        macros: List[str] = []
        for agent_name in self.rules.agents:
            macros.extend(self.list_agent_remediation_macros(agent_name))
        return _deduplicate_preserve_order(macros)

    def audit_macro_catalog(self, available_macros: Iterable[str]) -> Dict[str, Any]:
        """Compare remediation macro requirements with ``available_macros`` from the macro system."""

        available_set = {str(name) for name in available_macros}
        missing_by_agent: Dict[str, List[str]] = {}

        for agent_name in self.rules.agents:
            required = self.list_agent_remediation_macros(agent_name)
            missing = [macro for macro in required if macro not in available_set]
            if missing:
                missing_by_agent[agent_name] = missing

        required_macros = self.list_all_remediation_macros()
        missing_macros = _deduplicate_preserve_order(
            macro for macros in missing_by_agent.values() for macro in macros
        )
        unused_available = _deduplicate_preserve_order(
            macro for macro in sorted(available_set) if macro not in required_macros
        )

        return {
            "missing": missing_by_agent,
            "missing_macros": missing_macros,
            "required_macros": required_macros,
            "unused_available": unused_available,
        }

    def generate_health_report(self) -> Dict[str, Any]:
        """Return a summary of agent trust, failures, and QA rule expectations."""

        agents_report: Dict[str, Any] = {}
        for agent_name, budget in self.rules.agents.items():
            metric_details: Dict[str, Any] = {}
            for metric_name, threshold in budget.budgets.items():
                policy = budget.get_metric_policy(metric_name)
                metric_details[metric_name] = {
                    "threshold": threshold,
                    "comparison": policy.resolved_comparison() if policy else "auto",
                    "weight": policy.normalised_weight() if policy else 1.0,
                    "remediation_steps": list(policy.remediation_steps) if policy else [],
                    "remediation_macros": list(policy.remediation_macros) if policy else [],
                }

            agents_report[agent_name] = {
                "trust": self.get_agent_trust(agent_name),
                "failures": list(self.agent_failures.get(agent_name, [])),
                "budgets": dict(budget.budgets),
                "tests": list(budget.tests),
                "metrics": metric_details,
                "recommended_macros": self.list_agent_remediation_macros(agent_name),
            }

        return {
            "rules_version": self.rules.version,
            "agents": agents_report,
        }


def _deduplicate_preserve_order(values: Iterable[str]) -> List[str]:
    """Return ``values`` without duplicates while preserving the original order."""

    seen: Set[str] = set()
    ordered: List[str] = []
    for value in values:
        if not value:
            continue
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered
