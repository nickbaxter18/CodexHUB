"""
SECTION 1: Header & Purpose
- Tests for metric computations and threshold evaluation logic.
"""

# SECTION 2: Imports / Dependencies
import math

from src.common.config_loader import MetricsConfig, MetricThreshold
from src.training.metrics import MetricResult, compute_classification_metrics, evaluate_thresholds

# SECTION 3: Types / Interfaces / Schemas
# - Uses MetricThreshold and MetricsConfig schemas to emulate governance configuration.

# SECTION 4: Core Logic / Implementation


def test_compute_classification_metrics() -> None:
    y_true = [0, 1, 0, 1]
    y_pred = [0, 1, 1, 1]
    y_proba = [0.2, 0.8, 0.7, 0.6]
    metrics = compute_classification_metrics(y_true, y_pred, y_proba)
    assert math.isclose(metrics["accuracy"], 0.75)
    assert math.isclose(metrics["roc_auc"], 0.75)


def test_evaluate_thresholds_flags_failure() -> None:
    metrics_config = MetricsConfig(
        core_metrics={"accuracy": MetricThreshold(minimum=0.9)},
        fairness_metrics={},
    )
    computed = {"accuracy": 0.8}
    results = evaluate_thresholds(computed, metrics_config)
    assert isinstance(results["accuracy"], MetricResult)
    assert not results["accuracy"].passed


# SECTION 5: Error & Edge Case Handling
# - Ensures thresholds flag failing metrics correctly.


# SECTION 6: Performance Considerations
# - Uses tiny datasets for deterministic results.


# SECTION 7: No exports for test modules.
