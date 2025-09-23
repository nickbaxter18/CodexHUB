"""Unit tests for probabilistic QA utilities providing confidence-aware metrics."""

from __future__ import annotations

import math
from typing import List

import pytest

from qa_engine import (
    evaluate_metric,
    mean_confidence_interval,
    pass_probability,
    percentile,
    sample_mean_std,
    z_score,
)


def test_z_score_handles_zero_variance() -> None:
    """When variance is zero, z-score should reflect perfect certainty."""

    assert z_score(100.0, 0.0, 110.0) == math.inf
    assert z_score(100.0, 0.0, 90.0) == -math.inf


def test_pass_probability_matches_expected_values() -> None:
    """Validate probability calculation against known z-score thresholds."""

    assert pytest.approx(pass_probability(0.0), rel=1e-6) == 0.5
    assert pass_probability(2.0) > 0.97


def test_evaluate_metric_uses_confidence_threshold() -> None:
    """Metric evaluation should succeed only when confidence target is met."""

    distribution = {"mean": 250.0, "std": 30.0}
    assert evaluate_metric(300.0, distribution, 0.9) is True
    assert evaluate_metric(310.0, distribution, 0.99) is False


def test_sample_mean_std_matches_manual_computation() -> None:
    """Ensure mean/std helper aligns with manual calculations."""

    values: List[float] = [1.0, 2.0, 3.0, 4.0]
    mean, std = sample_mean_std(values)
    assert pytest.approx(mean, rel=1e-6) == 2.5
    assert pytest.approx(std, rel=1e-6) == 1.2909944487


def test_mean_confidence_interval_zero_variance() -> None:
    """Confidence interval collapses to the mean when variance is zero."""

    low, high = mean_confidence_interval([42.0, 42.0, 42.0])
    assert low == pytest.approx(high)
    assert low == pytest.approx(42.0)


def test_percentile_linear_interpolation() -> None:
    """Percentile helper should use linear interpolation for fractional ranks."""

    assert percentile([0.0, 10.0, 20.0, 30.0], 25.0) == 7.5
    assert percentile([1.0], 90.0) == 1.0
    assert percentile([], 50.0) == 0.0
