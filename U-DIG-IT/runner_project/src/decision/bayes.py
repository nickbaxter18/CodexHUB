"""Bayesian update helpers used by the decision agent."""

from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np
from numpy.typing import NDArray

from ..errors import DecisionError


def beta_update(alpha: float, beta: float, successes: int, failures: int) -> Tuple[float, float]:
    """Return posterior parameters for a Beta distribution."""

    if alpha <= 0 or beta <= 0:
        raise DecisionError("Alpha and beta must be positive for Beta updates")
    if successes < 0 or failures < 0:
        raise DecisionError("Successes and failures must be non-negative")
    return alpha + successes, beta + failures


def beta_mean(alpha: float, beta: float) -> float:
    if alpha <= 0 or beta <= 0:
        raise DecisionError("Alpha and beta must be positive")
    return alpha / (alpha + beta)


def normalize(weights: Iterable[float]) -> NDArray[np.float64]:
    arr = np.asarray(list(weights), dtype=float)
    if arr.size == 0:
        raise DecisionError("Cannot normalise empty weights")
    arr = np.maximum(arr, 0.0)
    total = arr.sum()
    if total == 0:
        return np.asarray(np.ones_like(arr, dtype=float) / max(arr.size, 1), dtype=float)
    return np.asarray(arr / total, dtype=float)


def bayesian_weighted_average(means: Iterable[float], weights: Iterable[float]) -> float:
    probs = normalize(weights)
    values = np.asarray(list(means), dtype=float)
    if values.size != probs.size:
        raise DecisionError("Means and weights must be the same length")
    return float(np.dot(values, probs))
