"""
SECTION 1: Header & Purpose
- Enforces QA policy thresholds with probabilistic confidence checks.
- Provides deterministic blocking decisions for CI/CD governance pipelines.
"""

from __future__ import annotations

# SECTION 2: Imports / Dependencies
import math
from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Tuple, TYPE_CHECKING

from qa_engine.probabilistic_qa import pass_probability, z_score

if TYPE_CHECKING:  # pragma: no cover - import used for type checking only
    from meta_agent.config_loader import ConfigLoader


# SECTION 3: Types / Interfaces / Schemas


@dataclass(frozen=True)
class PolicyDecision:
    """Represents the outcome of enforcing a single metric policy."""

    metric: str
    passed: bool
    observed: Optional[float]
    comparator: str
    threshold: Optional[float]
    confidence: float
    probability: Optional[float]
    reason: Optional[str]


@dataclass(frozen=True)
class PolicyEnforcementResult:
    """Aggregate result describing all metric policy decisions."""

    decisions: Tuple[PolicyDecision, ...]

    @property
    def passed(self) -> bool:
        """Return ``True`` when all policy decisions passed."""

        return all(decision.passed for decision in self.decisions)

    @property
    def violations(self) -> Tuple[PolicyDecision, ...]:
        """Return the subset of decisions that failed enforcement."""

        return tuple(decision for decision in self.decisions if not decision.passed)


@dataclass(frozen=True)
class _PolicyRule:
    """Internal representation of a governance QA policy."""

    metric: str
    comparator: str
    threshold: Optional[float]
    confidence: float


# SECTION 4: Core Logic / Implementation


class PolicyEnforcer:
    """Evaluate QA metrics against governance policies with statistical guarantees."""

    def __init__(
        self,
        policies: Mapping[str, Mapping[str, float]],
        *,
        require_distributions: bool = True,
    ) -> None:
        self._rules: Dict[str, _PolicyRule] = {}
        self._require_distributions = require_distributions
        for metric, config in policies.items():
            self._rules[metric] = self._build_rule(metric, config)

    @classmethod
    def from_config_loader(
        cls,
        loader: "ConfigLoader",
        *,
        require_distributions: bool = True,
    ) -> "PolicyEnforcer":
        """Instantiate an enforcer using a ``ConfigLoader`` QA policy snapshot."""

        policies = loader.get_qa_policies()
        return cls(policies, require_distributions=require_distributions)

    def enforce(
        self,
        metrics: Mapping[str, float],
        distributions: Optional[Mapping[str, Mapping[str, float]]] = None,
    ) -> PolicyEnforcementResult:
        """Evaluate ``metrics`` and return a structured enforcement result."""

        decisions = []
        for metric, rule in self._rules.items():
            measurement = metrics.get(metric)
            distribution = distributions.get(metric) if distributions else None
            decisions.append(self._evaluate_rule(rule, measurement, distribution))
        return PolicyEnforcementResult(tuple(decisions))

    def _build_rule(self, metric: str, config: Mapping[str, float]) -> _PolicyRule:
        comparator, threshold = self._resolve_threshold(metric, config)
        confidence = float(config.get("confidence", 1.0))
        confidence = min(max(confidence, 0.0), 1.0)
        return _PolicyRule(metric=metric, comparator=comparator, threshold=threshold, confidence=confidence)

    def _resolve_threshold(self, metric: str, config: Mapping[str, float]) -> Tuple[str, Optional[float]]:
        if "threshold" in config:
            return "<=", float(config["threshold"])
        if "max_vulns" in config:
            return "<=", float(config["max_vulns"])
        if "min_ratio" in config:
            return ">=", float(config["min_ratio"])
        return "==", None

    def _evaluate_rule(
        self,
        rule: _PolicyRule,
        measurement: Optional[float],
        distribution: Optional[Mapping[str, float]],
    ) -> PolicyDecision:
        if measurement is None:
            return PolicyDecision(
                metric=rule.metric,
                passed=False,
                observed=None,
                comparator=rule.comparator,
                threshold=rule.threshold,
                confidence=rule.confidence,
                probability=None,
                reason="measurement missing",
            )

        try:
            observed = float(measurement)
        except (TypeError, ValueError):
            return PolicyDecision(
                metric=rule.metric,
                passed=False,
                observed=None,
                comparator=rule.comparator,
                threshold=rule.threshold,
                confidence=rule.confidence,
                probability=None,
                reason="non-numeric measurement",
            )

        deterministic_pass, deterministic_reason = self._deterministic_check(rule, observed)
        probability, probability_pass, probability_reason = self._probabilistic_check(rule, distribution)

        passed = deterministic_pass and probability_pass
        reason = None
        if not deterministic_pass:
            reason = deterministic_reason
        elif not probability_pass:
            reason = probability_reason

        return PolicyDecision(
            metric=rule.metric,
            passed=passed,
            observed=observed,
            comparator=rule.comparator,
            threshold=rule.threshold,
            confidence=rule.confidence,
            probability=probability,
            reason=reason,
        )

    def _deterministic_check(self, rule: _PolicyRule, observed: float) -> Tuple[bool, Optional[str]]:
        threshold = rule.threshold
        comparator = rule.comparator
        if comparator == "<=" and threshold is not None:
            if observed <= threshold:
                return True, None
            return False, f"observed {observed} exceeds maximum {threshold}"
        if comparator == ">=" and threshold is not None:
            if observed >= threshold:
                return True, None
            return False, f"observed {observed} below minimum {threshold}"
        if comparator == "==" and threshold is not None:
            if observed == threshold:
                return True, None
            return False, f"observed {observed} does not equal required {threshold}"
        return True, None

    def _probabilistic_check(
        self,
        rule: _PolicyRule,
        distribution: Optional[Mapping[str, float]],
    ) -> Tuple[Optional[float], bool, Optional[str]]:
        if distribution is None:
            if self._require_distributions:
                return None, False, "distribution data missing"
            return None, True, None

        mean = distribution.get("mean")
        std = distribution.get("std")
        if not self._is_valid_number(mean) or not self._is_valid_number(std):
            return None, False, "distribution parameters invalid"

        threshold = rule.threshold if rule.threshold is not None else 0.0
        probability = self._calculate_probability(float(mean), float(std), threshold, rule.comparator)
        if probability is None:
            return None, False, "unable to compute probability"
        if probability >= rule.confidence:
            return probability, True, None
        return probability, False, (
            f"confidence {probability:.3f} below required {rule.confidence:.3f}"
        )

    @staticmethod
    def _calculate_probability(
        mean: float, std: float, threshold: float, comparator: str
    ) -> Optional[float]:
        if std < 0 or not math.isfinite(threshold):
            return None
        z = z_score(mean, std, threshold)
        probability = pass_probability(z)
        if comparator == ">=":
            probability = 1.0 - probability
        probability = max(0.0, min(1.0, probability))
        return probability

    @staticmethod
    def _is_valid_number(value: Optional[float]) -> bool:
        if value is None:
            return False
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return False
        return math.isfinite(numeric)


# SECTION 5: Error & Edge Case Handling
# - Missing measurements fail fast with descriptive reasons.
# - Non-numeric distributions or negative standard deviations are rejected.
# - Probability calculations clamp to [0, 1] to avoid floating point drift.


# SECTION 6: Performance Considerations
# - Policy evaluation is O(n) over configured metrics with constant-time math operations.
# - The enforcer caches parsed rules to avoid per-evaluation allocations.


# SECTION 7: Exports / Public API
__all__ = [
    "PolicyDecision",
    "PolicyEnforcementResult",
    "PolicyEnforcer",
]

