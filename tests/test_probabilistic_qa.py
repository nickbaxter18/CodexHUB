"""Unit tests for probabilistic QA utilities providing confidence-aware metrics."""

from __future__ import annotations

import math
from typing import List

import pytest

from qa_engine import (
    QAConfidenceReport,
    apply_calibration,
    brier_score,
    confidence_report,
    evaluate_calibrated_metric,
    evaluate_metric,
    expected_calibration_error,
    mean_confidence_interval,
    pass_probability,
    percentile,
    platt_calibration,
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


def test_platt_calibration_generates_monotonic_probabilities() -> None:
    """Calibration should produce probabilities that respect ordering of scores."""

    scores = [-3.0, -1.0, 0.0, 1.0, 3.0]
    labels = [0, 0, 0, 1, 1]
    calibration = platt_calibration(scores, labels, min_samples=5)
    probabilities = apply_calibration(scores, calibration)
    assert probabilities[0] < probabilities[1] < probabilities[2] < probabilities[-1]
    assert 0.0 <= probabilities[0] < 0.5
    assert 0.5 < probabilities[-1] <= 1.0


def test_evaluate_metric_prefers_calibrated_probabilities() -> None:
    """Calibration metadata within the distribution should drive evaluation."""

    scores = [-1.0, 0.0, 1.0, 2.0]
    labels = [0, 0, 1, 1]
    calibration = platt_calibration(scores, labels, min_samples=4)
    distribution = {"calibration": calibration.as_dict()}
    assert evaluate_metric(2.0, distribution, 0.7) is True
    assert evaluate_metric(-2.0, distribution, 0.7) is False


def test_confidence_report_summarises_probabilities() -> None:
    """Confidence report should expose probability averages and calibration metrics."""

    probabilities = [0.8, 0.7, 0.9, 0.4]
    labels = [1, 1, 1, 0]
    report = confidence_report(
        probabilities, labels, confidence_level=0.9, bootstrap_iterations=200
    )
    assert isinstance(report, QAConfidenceReport)
    assert report.samples == 4
    assert report.brier_score == pytest.approx(brier_score(probabilities, labels), rel=1e-6)
    assert 0.0 <= report.calibration_error <= 0.5


def test_evaluate_calibrated_metric_returns_report_tuple() -> None:
    """Calibrated evaluation should surface probability, report, and pass/fail."""

    scores = [-2.0, -1.0, 0.5, 1.5, 2.5]
    labels = [0, 0, 1, 1, 1]
    calibration = platt_calibration(scores, labels, min_samples=5)
    passed, report, probability = evaluate_calibrated_metric(
        1.0,
        calibration,
        scores,
        labels,
        confidence=0.6,
        bootstrap_iterations=200,
    )
    assert isinstance(report, QAConfidenceReport)
    assert isinstance(passed, bool)
    assert 0.0 <= probability <= 1.0
    assert report.meets_confidence(0.2) in {True, False}


def test_expected_calibration_error_handles_perfect_calibration() -> None:
    """ECE should be near zero when probabilities equal observed outcomes."""

    probabilities = [0.0, 1.0, 0.0, 1.0]
    labels = [0, 1, 0, 1]
    assert expected_calibration_error(probabilities, labels, bins=2) == pytest.approx(0.0, abs=1e-9)


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
