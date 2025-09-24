"""Probabilistic QA engine package exposing uncertainty-aware utilities."""

# === Header & Purpose ===
# Aggregates helper modules that interpret QA metrics as probability
# distributions for trust-aware decision making.

from .probabilistic_qa import (
    CalibrationResult,
    QAConfidenceReport,
    apply_calibration,
    brier_score,
    confidence_report,
    evaluate_calibrated_metric,
    evaluate_metric,
    expected_calibration_error,
    pass_probability,
    platt_calibration,
    z_score,
)
from .statistics_helpers import (
    bootstrap_confidence_interval,
    clamp_probability,
    mean_confidence_interval,
    percentile,
    sample_mean_std,
)

__all__ = [
    "CalibrationResult",
    "QAConfidenceReport",
    "apply_calibration",
    "brier_score",
    "confidence_report",
    "evaluate_calibrated_metric",
    "evaluate_metric",
    "expected_calibration_error",
    "pass_probability",
    "platt_calibration",
    "z_score",
    "bootstrap_confidence_interval",
    "clamp_probability",
    "mean_confidence_interval",
    "percentile",
    "sample_mean_std",
]
