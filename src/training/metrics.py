"""
SECTION 1: Header & Purpose
- Provides deterministic evaluation metrics for training and governance validation.
- Integrates with fairness assessments and registry logging workflows.
"""

from __future__ import annotations

# SECTION 2: Imports / Dependencies
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping

import numpy as np
from sklearn import metrics as sk_metrics

from src.common.config_loader import MetricsConfig, MetricThreshold

# SECTION 3: Types / Interfaces / Schemas


@dataclass(frozen=True)
class MetricResult:
    """Represents the outcome of a single metric computation."""

    name: str
    value: float
    passed: bool
    threshold: MetricThreshold | None


# SECTION 4: Core Logic / Implementation


def compute_classification_metrics(
    y_true: Iterable[int] | Iterable[float],
    y_pred: Iterable[int],
    y_proba: Iterable[float] | None = None,
) -> Dict[str, float]:
    """Compute standard classification metrics."""

    y_true_arr = np.asarray(list(y_true))
    y_pred_arr = np.asarray(list(y_pred))
    metrics: Dict[str, float] = {
        "accuracy": sk_metrics.accuracy_score(y_true_arr, y_pred_arr),
        "precision": sk_metrics.precision_score(y_true_arr, y_pred_arr, zero_division=0),
        "recall": sk_metrics.recall_score(y_true_arr, y_pred_arr, zero_division=0),
        "f1": sk_metrics.f1_score(y_true_arr, y_pred_arr, zero_division=0),
    }
    if y_proba is not None:
        y_proba_arr = np.asarray(list(y_proba))
        metrics["roc_auc"] = sk_metrics.roc_auc_score(y_true_arr, y_proba_arr)
    return metrics


def evaluate_thresholds(
    computed_metrics: Mapping[str, float], config: MetricsConfig
) -> Dict[str, MetricResult]:
    """Validate metric values against governance thresholds."""

    outcomes: Dict[str, MetricResult] = {}
    for name, value in computed_metrics.items():
        threshold = config.core_metrics.get(name) or config.fairness_metrics.get(name)
        passed = _passes_threshold(value, threshold)
        outcomes[name] = MetricResult(name=name, value=value, passed=passed, threshold=threshold)
    return outcomes


# SECTION 5: Error & Edge Case Handling
# - Metrics gracefully handle division by zero via zero_division configuration.
# - Missing thresholds are treated as passes to avoid false failure states.


# SECTION 6: Performance Considerations
# - Utilizes NumPy arrays for vectorized metrics with O(n) runtime and low overhead.
# - Avoids repeated conversions by normalizing inputs once per call.


# SECTION 7: Exports / Public API
__all__ = [
    "MetricResult",
    "compute_classification_metrics",
    "evaluate_thresholds",
]


def _passes_threshold(value: float, threshold: MetricThreshold | None) -> bool:
    """Check whether a metric value satisfies configured bounds."""

    if threshold is None:
        return True
    if threshold.minimum is not None and value < threshold.minimum:
        return False
    if threshold.maximum is not None and value > threshold.maximum:
        return False
    return True
