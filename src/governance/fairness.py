"""
SECTION 1: Header & Purpose
    - Provides fairness metrics such as statistical parity difference and equal opportunity gap.
    - Applies governance thresholds to flag bias issues before deployment.
"""

from __future__ import annotations

# SECTION 2: Imports / Dependencies
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping

import numpy as np
import numpy.typing as npt

from src.common.config_loader import FairnessGovernanceConfig, MetricsConfig, MetricThreshold

# SECTION 3: Types / Interfaces / Schemas

ArrayAny = npt.NDArray[Any]
BoolArray = npt.NDArray[np.bool_]


@dataclass(frozen=True)
class FairnessMetricResult:
    """Describes the outcome of a fairness metric evaluation."""

    name: str
    value: float
    passed: bool
    threshold: MetricThreshold | None
    details: Dict[str, float]

    def to_dict(self) -> Dict[str, object]:
        """Serialise the fairness metric result for reporting and governance exports."""

        return {
            "name": self.name,
            "value": self.value,
            "passed": self.passed,
            "threshold": self.threshold.model_dump() if self.threshold else None,
            "details": dict(self.details),
        }


# SECTION 4: Core Logic / Implementation


def evaluate_fairness(
    y_true: Iterable[int],
    y_pred: Iterable[int],
    sensitive_attribute: Iterable[str | int],
    metrics_config: MetricsConfig,
    fairness_config: FairnessGovernanceConfig,
) -> Dict[str, FairnessMetricResult]:
    """Compute fairness metrics and evaluate them against configured thresholds."""

    y_true_arr: ArrayAny = np.asarray(list(y_true))
    y_pred_arr: ArrayAny = np.asarray(list(y_pred))
    sensitive_arr: ArrayAny = np.asarray(list(sensitive_attribute))
    _validate_input_lengths(y_true_arr, y_pred_arr, sensitive_arr)

    group_mask = _group_masks(sensitive_arr)
    filtered_masks = {
        group: mask
        for group, mask in group_mask.items()
        if mask.sum() >= fairness_config.min_samples_per_group
    }
    if not filtered_masks:
        raise ValueError("No groups satisfy min_samples_per_group requirement")
    group_positive_rates: Dict[str | int, float] = {
        group: float(y_pred_arr[mask].mean()) for group, mask in filtered_masks.items()
    }
    group_true_positive_rates = _true_positive_rates(y_true_arr, y_pred_arr, filtered_masks)

    metrics: Dict[str, FairnessMetricResult] = {}

    parity_value = _statistical_parity_difference(group_positive_rates)
    parity_threshold = metrics_config.fairness_metrics.get("statistical_parity_difference")
    metrics["statistical_parity_difference"] = _build_result(
        name="statistical_parity_difference",
        value=parity_value,
        threshold=parity_threshold,
        details=group_positive_rates,
        enforce=fairness_config.enforce,
    )

    opportunity_value = _equal_opportunity_difference(group_true_positive_rates)
    opportunity_threshold = metrics_config.fairness_metrics.get("equal_opportunity_difference")
    metrics["equal_opportunity_difference"] = _build_result(
        name="equal_opportunity_difference",
        value=opportunity_value,
        threshold=opportunity_threshold,
        details=group_true_positive_rates,
        enforce=fairness_config.enforce,
    )

    disparity_value = _disparate_impact_ratio(group_positive_rates)
    disparity_threshold = metrics_config.fairness_metrics.get("disparate_impact_ratio")
    metrics["disparate_impact_ratio"] = _build_result(
        name="disparate_impact_ratio",
        value=disparity_value,
        threshold=disparity_threshold,
        details=group_positive_rates,
        enforce=fairness_config.enforce,
    )

    return metrics


# SECTION 5: Error & Edge Case Handling
# - Validates array lengths to prevent silent broadcasting errors.
# - Enforces minimum sample requirements and raises descriptive errors when unmet.
# - Avoids division-by-zero by guarding disparate impact calculations.
# - Defaults to neutral values when necessary.


# SECTION 6: Performance Considerations
# - Utilizes NumPy vectorization for O(n) fairness computations.
# - Precomputes group masks once to reuse across metrics.


# SECTION 7: Exports / Public API
__all__ = ["FairnessMetricResult", "evaluate_fairness"]


def _validate_input_lengths(y_true: ArrayAny, y_pred: ArrayAny, sensitive: ArrayAny) -> None:
    """Ensure all inputs share identical lengths."""

    if not (len(y_true) == len(y_pred) == len(sensitive)):
        raise ValueError("y_true, y_pred, and sensitive_attribute must be the same length")


def _group_masks(sensitive: ArrayAny) -> Dict[str | int, BoolArray]:
    """Generate boolean masks for each sensitive attribute value."""

    masks: Dict[str | int, BoolArray] = {}
    for group in np.unique(sensitive):
        masks[group] = np.asarray(sensitive == group, dtype=bool)
    return masks


def _true_positive_rates(
    y_true: ArrayAny, y_pred: ArrayAny, masks: Mapping[str | int, BoolArray]
) -> Dict[str | int, float]:
    """Calculate true positive rates for each group."""

    rates: Dict[str | int, float] = {}
    for group, mask in masks.items():
        positives = y_true[mask] == 1
        if positives.sum() == 0:
            rates[group] = 0.0
            continue
        rates[group] = (y_pred[mask][positives]).mean() if positives.sum() else 0.0
    return rates


def _statistical_parity_difference(group_rates: Mapping[str | int, float]) -> float:
    """Return the absolute difference between max and min group positive rates."""

    if not group_rates:
        return 0.0
    return float(max(group_rates.values()) - min(group_rates.values()))


def _equal_opportunity_difference(group_true_positive_rates: Mapping[str | int, float]) -> float:
    """Return the absolute difference between max and min true positive rates."""

    if not group_true_positive_rates:
        return 0.0
    return float(max(group_true_positive_rates.values()) - min(group_true_positive_rates.values()))


def _disparate_impact_ratio(group_rates: Mapping[str | int, float]) -> float:
    """Return the ratio between minimum and maximum group positive rates."""

    if not group_rates:
        return 1.0
    max_rate = max(group_rates.values())
    min_rate = min(group_rates.values())
    if max_rate == 0:
        return 1.0
    return float(min_rate / max_rate)


def _build_result(
    name: str,
    value: float,
    threshold: MetricThreshold | None,
    details: Mapping[str | int, float],
    enforce: bool,
) -> FairnessMetricResult:
    """Construct a FairnessMetricResult respecting enforcement flags."""

    passed = True if not enforce else _passes_threshold(value, threshold)
    normalized_details = {str(group): float(rate) for group, rate in details.items()}
    return FairnessMetricResult(
        name=name,
        value=value,
        passed=passed,
        threshold=threshold,
        details=normalized_details,
    )


def _passes_threshold(value: float, threshold: MetricThreshold | None) -> bool:
    """Evaluate thresholds similar to training metrics."""

    if threshold is None:
        return True
    if threshold.minimum is not None and value < threshold.minimum:
        return False
    if threshold.maximum is not None and value > threshold.maximum:
        return False
    return True
