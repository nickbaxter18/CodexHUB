"""Functions for interpreting QA metrics as probability distributions."""

# === Header & Purpose ===
# Translate deterministic QA metrics into probabilistic signals using standard
# normal approximations so that governance policies can reason about confidence
# and uncertainty when enforcing thresholds.

# === Imports / Dependencies ===
from __future__ import annotations

import math
from typing import Dict

from .statistics_helpers import cumulative_standard_normal


# === Types, Interfaces, Contracts ===
def z_score(mean: float, std_dev: float, threshold: float) -> float:
    """Compute the z-score comparing ``threshold`` against a normal distribution."""

    if std_dev == 0:
        return math.inf if threshold >= mean else -math.inf
    return (threshold - mean) / std_dev


def pass_probability(z: float) -> float:
    """Return the one-sided probability of passing given a z-score."""

    return cumulative_standard_normal(z)


def evaluate_metric(value: float, distribution: Dict[str, float], confidence: float) -> bool:
    """Determine whether ``value`` meets ``confidence`` given distribution moments."""

    mean = float(distribution.get("mean", value))
    std = float(distribution.get("std", 0.0))
    z = z_score(mean, std, value)
    probability = pass_probability(z)
    return probability >= confidence


# === Error & Edge Case Handling ===
# - Zero variance distributions treat values above the mean as certain failures.
# - Missing mean/std defaults to the observed value to avoid false positives.


# === Performance Considerations ===
# - Functions operate in constant time and are safe for tight event loops.


# === Exports / Public API ===
__all__ = ["z_score", "pass_probability", "evaluate_metric"]
