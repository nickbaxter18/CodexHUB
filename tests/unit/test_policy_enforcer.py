"""
SECTION 1: Header & Purpose
- Unit tests for governance policy enforcement with probabilistic QA thresholds.
"""

# SECTION 2: Imports / Dependencies
from pathlib import Path

import pytest

try:  # pragma: no cover - optional dependency for integration coverage
    from meta_agent.config_loader import ConfigLoader
except ModuleNotFoundError:  # pragma: no cover - jsonschema optional in some environments
    ConfigLoader = None  # type: ignore[assignment]

from src.governance.policy_enforcer import (
    PolicyEnforcementResult,
    PolicyEnforcer,
)


# SECTION 3: Types / Interfaces / Schemas
# - Uses PolicyEnforcementResult dataclass to assert structured outcomes.


def _build_enforcer(require_distributions: bool = True) -> PolicyEnforcer:
    policies = {
        "latency_ms": {"threshold": 300.0, "confidence": 0.95},
        "contrast_ratio": {"min_ratio": 4.5, "confidence": 0.9},
    }
    return PolicyEnforcer(policies, require_distributions=require_distributions)


# SECTION 4: Core Logic / Implementation


def test_policy_enforcer_passes_when_thresholds_and_confidence_met() -> None:
    enforcer = _build_enforcer()
    metrics = {"latency_ms": 250.0, "contrast_ratio": 4.8}
    distributions = {
        "latency_ms": {"mean": 230.0, "std": 15.0},
        "contrast_ratio": {"mean": 5.0, "std": 0.1},
    }

    result = enforcer.enforce(metrics, distributions)

    assert isinstance(result, PolicyEnforcementResult)
    assert result.passed is True
    assert all(decision.probability is not None for decision in result.decisions)


def test_policy_enforcer_detects_threshold_violation() -> None:
    enforcer = _build_enforcer()
    metrics = {"latency_ms": 320.0, "contrast_ratio": 5.0}
    distributions = {
        "latency_ms": {"mean": 200.0, "std": 15.0},
        "contrast_ratio": {"mean": 5.0, "std": 0.1},
    }

    result = enforcer.enforce(metrics, distributions)
    failure = result.violations[0]

    assert failure.metric == "latency_ms"
    assert failure.passed is False
    assert "exceeds" in (failure.reason or "")


def test_policy_enforcer_detects_low_confidence() -> None:
    enforcer = _build_enforcer()
    metrics = {"latency_ms": 240.0, "contrast_ratio": 4.8}
    distributions = {
        "latency_ms": {"mean": 240.0, "std": 10.0},
        "contrast_ratio": {"mean": 4.7, "std": 0.5},
    }

    result = enforcer.enforce(metrics, distributions)

    assert any("confidence" in (decision.reason or "") for decision in result.violations)


def test_policy_enforcer_blocks_when_distribution_missing() -> None:
    enforcer = _build_enforcer(require_distributions=True)
    metrics = {"latency_ms": 240.0, "contrast_ratio": 4.8}

    result = enforcer.enforce(metrics, distributions={})

    assert result.passed is False
    assert any("distribution" in (decision.reason or "") for decision in result.decisions)


def test_policy_enforcer_allows_missing_distribution_when_configured() -> None:
    enforcer = _build_enforcer(require_distributions=False)
    metrics = {"latency_ms": 240.0, "contrast_ratio": 4.8}

    result = enforcer.enforce(metrics, distributions={})

    assert result.passed is True
    assert all(decision.probability is None for decision in result.decisions)


@pytest.mark.skipif(ConfigLoader is None, reason="ConfigLoader dependencies not available")
def test_policy_enforcer_from_config_loader() -> None:
    loader = ConfigLoader(config_dir=Path("config"))
    enforcer = PolicyEnforcer.from_config_loader(loader)

    metrics = {
        "latency_ms_p95": 260.0,
        "accessibility_contrast_ratio": 5.1,
        "security_vuln_count": 0.0,
    }
    distributions = {
        "latency_ms_p95": {"mean": 240.0, "std": 10.0},
        "accessibility_contrast_ratio": {"mean": 5.5, "std": 0.1},
        "security_vuln_count": {"mean": 0.0, "std": 0.0},
    }

    result = enforcer.enforce(metrics, distributions)

    assert result.passed is True
    assert {decision.metric for decision in result.decisions} >= metrics.keys()


# SECTION 5: Error & Edge Case Handling
# - Ensures deterministic and probabilistic failures surface descriptive reasons.
# - Validates behaviour when distribution inputs are optional.


# SECTION 6: Performance Considerations
# - Tests operate on a tiny number of policies ensuring negligible runtime.


# SECTION 7: No exports for test modules.
