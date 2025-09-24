from __future__ import annotations

"""Probabilistic QA utilities offering calibration and confidence scoring."""

# === Header & Purpose ===
# Translate deterministic QA metrics into probabilistic signals and provide
# calibrated confidence reports that can be enforced by governance policies.

# === Imports / Dependencies ===

import math
from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple, Union

import numpy as np

from .statistics_helpers import (
    bootstrap_confidence_interval,
    clamp_probability,
    cumulative_standard_normal,
)


# === Types, Interfaces, Contracts ===
@dataclass(frozen=True)
class CalibrationResult:
    """Logistic calibration parameters derived from Platt scaling."""

    intercept: float
    slope: float
    iterations: int
    converged: bool
    loss: float

    def predict(self, scores: Union[Sequence[float], float]) -> np.ndarray:
        """Return calibrated probabilities for ``scores``."""

        array = np.asarray(scores, dtype=float)
        logits = np.clip(self.intercept + self.slope * array, -50.0, 50.0)
        return _sigmoid(logits)

    def as_dict(self) -> Dict[str, Union[bool, float, int]]:
        """Return a serialisable representation of the calibration."""

        return {
            "intercept": float(self.intercept),
            "slope": float(self.slope),
            "iterations": int(self.iterations),
            "converged": bool(self.converged),
            "loss": float(self.loss),
        }


@dataclass(frozen=True)
class QAConfidenceReport:
    """Summary of calibrated QA performance."""

    mean_probability: float
    lower_bound: float
    upper_bound: float
    observed_rate: float
    brier_score: float
    calibration_error: float
    samples: int

    def meets_confidence(self, target: float) -> bool:
        """Return ``True`` when the lower bound satisfies ``target``."""

        return self.lower_bound >= target

    def as_dict(self) -> Dict[str, Union[float, int]]:
        """Return a serialisable representation of the report."""

        return {
            "mean_probability": float(self.mean_probability),
            "lower_bound": float(self.lower_bound),
            "upper_bound": float(self.upper_bound),
            "observed_rate": float(self.observed_rate),
            "brier_score": float(self.brier_score),
            "calibration_error": float(self.calibration_error),
            "samples": int(self.samples),
        }


# === Core Logic / Implementation ===


def z_score(mean: float, std_dev: float, threshold: float) -> float:
    """Compute the z-score comparing ``threshold`` against a normal distribution."""

    if std_dev == 0:
        return math.inf if threshold >= mean else -math.inf
    return (threshold - mean) / std_dev


def pass_probability(z: float) -> float:
    """Return the one-sided probability of passing given a z-score."""

    return cumulative_standard_normal(z)


def evaluate_metric(value: float, distribution: Dict[str, float], confidence: float) -> bool:
    """Determine whether ``value`` satisfies ``confidence`` using available signals."""

    if "calibration" in distribution:
        calibration = _ensure_calibration(distribution["calibration"])
        probability = float(calibration.predict([value])[0])
        return probability >= confidence

    probability = float(distribution.get("probability", float("nan")))
    if math.isfinite(probability):
        return probability >= confidence

    mean = float(distribution.get("mean", value))
    std = float(distribution.get("std", 0.0))
    z = z_score(mean, std, value)
    probability = pass_probability(z)
    return probability >= confidence


def platt_calibration(
    scores: Sequence[float],
    labels: Sequence[Union[bool, int, float]],
    *,
    min_samples: int = 10,
    max_iter: int = 100,
    tol: float = 1e-6,
    regularization: float = 1e-6,
) -> CalibrationResult:
    """Return Platt scaling parameters for ``scores`` and binary ``labels``."""

    score_array, label_array = _prepare_training_data(scores, labels)
    if score_array.size < min_samples:
        raise ValueError("insufficient samples for calibration")

    positives = float(label_array.sum())
    negatives = float(label_array.size - positives)
    if positives == 0.0 or negatives == 0.0:
        prior = clamp_probability((positives + 1.0) / (label_array.size + 2.0))
        intercept = math.log(prior / (1.0 - prior))
        probabilities = np.full(label_array.shape, prior, dtype=float)
        loss = _log_loss(probabilities, label_array, regularization, np.array([intercept, 0.0]))
        return CalibrationResult(
            intercept=intercept, slope=0.0, iterations=0, converged=True, loss=loss
        )

    design = np.column_stack([np.ones_like(score_array), score_array])
    weights = np.zeros(2, dtype=float)
    converged = False
    iterations_used = 0

    for iteration in range(1, max_iter + 1):
        logits = np.clip(design @ weights, -50.0, 50.0)
        probabilities = _sigmoid(logits)
        gradient = design.T @ (probabilities - label_array) + regularization * weights
        W = probabilities * (1.0 - probabilities)
        if np.all(W < 1e-12):
            break
        h00 = np.sum(W * design[:, 0] * design[:, 0]) + regularization
        h01 = np.sum(W * design[:, 0] * design[:, 1])
        h11 = np.sum(W * design[:, 1] * design[:, 1]) + regularization
        hessian = np.array([[h00, h01], [h01, h11]])
        try:
            delta = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            hessian += np.eye(2) * (regularization * 10.0)
            delta = np.linalg.solve(hessian, gradient)
        weights -= delta
        iterations_used = iteration
        if float(np.linalg.norm(delta, ord=2)) <= tol:
            converged = True
            break

    logits = np.clip(design @ weights, -50.0, 50.0)
    probabilities = _sigmoid(logits)
    loss = _log_loss(probabilities, label_array, regularization, weights)
    return CalibrationResult(
        intercept=float(weights[0]),
        slope=float(weights[1]),
        iterations=iterations_used,
        converged=converged,
        loss=loss,
    )


def apply_calibration(
    scores: Sequence[float], calibration: Union[CalibrationResult, Dict[str, float]]
) -> np.ndarray:
    """Return calibrated probabilities for ``scores``."""

    calibration_result = _ensure_calibration(calibration)
    return calibration_result.predict(scores)


def brier_score(probabilities: Sequence[float], labels: Sequence[Union[bool, int, float]]) -> float:
    """Return the Brier score for ``probabilities`` against ``labels``."""

    prob_array, label_array = _align_probabilities(probabilities, labels)
    if prob_array.size == 0:
        return 0.0
    diff = prob_array - label_array
    return float(np.mean(diff * diff))


def expected_calibration_error(
    probabilities: Sequence[float],
    labels: Sequence[Union[bool, int, float]],
    *,
    bins: int = 10,
) -> float:
    """Return the Expected Calibration Error (ECE) for ``probabilities``."""

    if bins <= 0:
        raise ValueError("bins must be positive")
    prob_array, label_array = _align_probabilities(probabilities, labels)
    if prob_array.size == 0:
        return 0.0
    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    total = float(prob_array.size)
    for index in range(bins):
        lower = edges[index]
        upper = edges[index + 1]
        if index == bins - 1:
            mask = (prob_array >= lower) & (prob_array <= upper)
        else:
            mask = (prob_array >= lower) & (prob_array < upper)
        if not np.any(mask):
            continue
        bin_prob = float(np.mean(prob_array[mask]))
        bin_acc = float(np.mean(label_array[mask]))
        weight = float(np.sum(mask)) / total
        ece += weight * abs(bin_prob - bin_acc)
    return float(ece)


def confidence_report(
    probabilities: Sequence[float],
    labels: Sequence[Union[bool, int, float]],
    *,
    confidence_level: float = 0.95,
    bootstrap_iterations: int = 1000,
    bins: int = 10,
    random_state: Optional[int] = None,
) -> QAConfidenceReport:
    """Return a confidence report aggregating calibration quality metrics."""

    prob_array, label_array = _align_probabilities(probabilities, labels)
    if prob_array.size == 0:
        return QAConfidenceReport(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0)

    mean_probability = float(np.mean(prob_array))
    observed_rate = float(np.mean(label_array))
    lower, upper = bootstrap_confidence_interval(
        prob_array,
        confidence=confidence_level,
        iterations=bootstrap_iterations,
        random_state=random_state,
    )
    brier = brier_score(prob_array, label_array)
    ece = expected_calibration_error(prob_array, label_array, bins=bins)
    return QAConfidenceReport(
        mean_probability, lower, upper, observed_rate, brier, ece, int(prob_array.size)
    )


def evaluate_calibrated_metric(
    value: float,
    calibration: Union[CalibrationResult, Dict[str, float]],
    historical_scores: Sequence[float],
    historical_labels: Sequence[Union[bool, int, float]],
    *,
    confidence: float = 0.95,
    bootstrap_iterations: int = 1000,
    bins: int = 10,
    random_state: Optional[int] = None,
) -> Tuple[bool, QAConfidenceReport, float]:
    """Evaluate ``value`` against calibrated confidence targets."""

    calibration_result = _ensure_calibration(calibration)
    probability = float(calibration_result.predict([value])[0])
    historical_probabilities = calibration_result.predict(historical_scores)
    report = confidence_report(
        historical_probabilities,
        historical_labels,
        confidence_level=confidence,
        bootstrap_iterations=bootstrap_iterations,
        bins=bins,
        random_state=random_state,
    )
    meets = probability >= confidence and report.meets_confidence(confidence)
    return meets, report, probability


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-values))


def _prepare_training_data(
    scores: Sequence[float], labels: Sequence[Union[bool, int, float]]
) -> Tuple[np.ndarray, np.ndarray]:
    raw_scores = np.asarray(scores, dtype=float)
    raw_labels = _coerce_labels(labels)
    if raw_scores.size != raw_labels.size:
        raise ValueError("scores and labels length mismatch")
    mask = np.isfinite(raw_scores)
    filtered_scores = raw_scores[mask]
    filtered_labels = raw_labels[mask]
    return filtered_scores, filtered_labels


def _coerce_labels(labels: Sequence[Union[bool, int, float]]) -> np.ndarray:
    coerced = np.empty(len(labels), dtype=float)
    for index, label in enumerate(labels):
        coerced[index] = 1.0 if bool(label) else 0.0
    return coerced


def _align_probabilities(
    probabilities: Sequence[float], labels: Sequence[Union[bool, int, float]]
) -> Tuple[np.ndarray, np.ndarray]:
    prob_array = np.asarray(probabilities, dtype=float)
    label_array = _coerce_labels(labels)
    if prob_array.size != label_array.size:
        raise ValueError("probabilities and labels length mismatch")
    mask = np.isfinite(prob_array)
    prob_array = np.clip(prob_array[mask], 0.0, 1.0)
    label_array = label_array[mask]
    return prob_array, label_array


def _ensure_calibration(
    calibration: Union[CalibrationResult, Dict[str, Union[bool, float, int]]],
) -> CalibrationResult:
    if isinstance(calibration, CalibrationResult):
        return calibration
    if not isinstance(calibration, dict):
        raise TypeError("calibration must be a CalibrationResult or mapping")
    try:
        intercept = float(calibration["intercept"])
        slope = float(calibration["slope"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("calibration mapping missing intercept/slope") from exc
    iterations = int(calibration.get("iterations", 0))
    converged = bool(calibration.get("converged", True))
    loss = float(calibration.get("loss", 0.0))
    return CalibrationResult(
        intercept=intercept,
        slope=slope,
        iterations=iterations,
        converged=converged,
        loss=loss,
    )


def _log_loss(
    probabilities: np.ndarray,
    labels: np.ndarray,
    regularization: float,
    weights: np.ndarray,
) -> float:
    clipped = np.clip(probabilities, 1e-15, 1.0 - 1e-15)
    loss = -np.sum(labels * np.log(clipped) + (1.0 - labels) * np.log(1.0 - clipped))
    loss += 0.5 * regularization * float(np.sum(weights * weights))
    return float(loss)


# === Error & Edge Case Handling ===
# - Calibration gracefully falls back to prior probabilities when classes are imbalanced.
# - Probability alignment ignores non-finite values and clips to [0, 1].
# - Evaluation defaults to distributional checks when calibration metadata is absent.


# === Performance Considerations ===
# - Calibration uses vectorised NumPy operations and converges in <100 iterations.
# - Confidence reporting reuses bootstrap helpers for statistical guarantees.


# === Exports / Public API ===
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
]
