"""Unit tests for statistical helper utilities supporting probabilistic QA."""

from __future__ import annotations

import math

import pytest

from qa_engine.statistics_helpers import (
    bootstrap_confidence_interval,
    clamp_probability,
    mean_confidence_interval,
    percentile,
    sample_mean_std,
)


def test_clamp_probability_handles_invalid_inputs() -> None:
    """Probabilities should be clamped within (0, 1) even for invalid inputs."""

    assert clamp_probability(-0.5) == pytest.approx(1e-15)
    assert clamp_probability(2.0) == pytest.approx(1.0 - 1e-15)
    assert clamp_probability(float("nan")) == pytest.approx(0.5)
    assert clamp_probability("0.75") == pytest.approx(0.75)


def test_bootstrap_confidence_interval_single_value_is_degenerate() -> None:
    """Bootstrap confidence should collapse when only one observation exists."""

    low, high = bootstrap_confidence_interval([42.0])
    assert low == pytest.approx(42.0)
    assert high == pytest.approx(42.0)


def test_bootstrap_confidence_interval_ignores_non_numeric_values() -> None:
    """Bootstrap routine should ignore invalid entries and respect random state."""

    low, high = bootstrap_confidence_interval(
        [1.0, 2.0, 3.0, float("nan"), None],
        confidence=0.8,
        iterations=200,
        random_state=123,
    )
    assert low <= high
    assert 1.0 <= low <= 3.0
    assert 1.0 <= high <= 3.0


def test_sample_mean_std_filters_non_finite_values() -> None:
    """Mean and standard deviation helpers should ignore non-finite entries."""

    mean, std = sample_mean_std([1.0, 2.0, "3.0", float("nan")])
    assert mean == pytest.approx(2.0)
    assert std == pytest.approx(math.sqrt(1.0), rel=1e-6)


def test_mean_confidence_interval_with_uniform_values() -> None:
    """Confidence interval collapses to the mean for uniform data."""

    low, high = mean_confidence_interval([10.0, 10.0, 10.0])
    assert low == pytest.approx(high)
    assert low == pytest.approx(10.0)


def test_percentile_handles_sparse_values() -> None:
    """Percentile helper should gracefully handle sparse sequences."""

    assert percentile([float("nan"), 5.0, 15.0, 30.0], 50.0) == pytest.approx(15.0)
    assert percentile([], 25.0) == pytest.approx(0.0)
