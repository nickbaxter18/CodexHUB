"""
SECTION 1: Header & Purpose
- Compliance tests validating fairness metric evaluations against governance thresholds.
"""

# SECTION 2: Imports / Dependencies
import pytest

from src.common.config_loader import FairnessGovernanceConfig, MetricsConfig, MetricThreshold
from src.governance.fairness import FairnessMetricResult, evaluate_fairness

# SECTION 3: Types / Interfaces / Schemas
# - Uses governance config schemas to configure fairness evaluation.

# SECTION 4: Core Logic / Implementation


def test_evaluate_fairness_within_thresholds() -> None:
    metrics_config = MetricsConfig(
        core_metrics={},
        fairness_metrics={
            "statistical_parity_difference": MetricThreshold(minimum=-0.2, maximum=0.2),
            "equal_opportunity_difference": MetricThreshold(minimum=-0.2, maximum=0.2),
            "disparate_impact_ratio": MetricThreshold(minimum=0.8, maximum=1.25),
        },
    )
    fairness_config = FairnessGovernanceConfig(
        enforce=True,
        sensitive_attributes=["demo"],
        min_samples_per_group=2,
    )
    y_true = [0, 1, 0, 1]
    y_pred = [0, 1, 0, 1]
    sensitive = ["A", "A", "B", "B"]

    results = evaluate_fairness(y_true, y_pred, sensitive, metrics_config, fairness_config)
    assert all(isinstance(result, FairnessMetricResult) for result in results.values())
    assert all(result.passed for result in results.values())


def test_evaluate_fairness_insufficient_samples() -> None:
    metrics_config = MetricsConfig(core_metrics={}, fairness_metrics={})
    fairness_config = FairnessGovernanceConfig(
        enforce=True,
        sensitive_attributes=["demo"],
        min_samples_per_group=3,
    )
    y_true = [0, 1]
    y_pred = [0, 1]
    sensitive = ["A", "B"]

    with pytest.raises(ValueError):
        evaluate_fairness(y_true, y_pred, sensitive, metrics_config, fairness_config)


# SECTION 5: Error & Edge Case Handling
# - Ensures insufficient sample sizes raise explicit errors.


# SECTION 6: Performance Considerations
# - Operates on tiny arrays keeping runtime negligible.


# SECTION 7: No exports for test modules.
