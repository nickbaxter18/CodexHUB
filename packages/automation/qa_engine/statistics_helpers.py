from __future__ import annotations

"""Statistical helper routines supporting probabilistic QA decisions."""

# === Header & Purpose ===
# Encapsulates statistical utilities shared across probabilistic QA analyses,
# including cumulative distributions, percentile computation, bootstrap
# estimation, and confidence interval construction with robust edge handling.

# === Imports / Dependencies ===

import math
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np


def _coerce_finite(values: Iterable[float]) -> List[float]:
    """Return a list of finite ``float`` values from ``values``."""

    cleaned: List[float] = []
    for value in values:
        try:
            numeric = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if math.isfinite(numeric):
            cleaned.append(numeric)
    return cleaned


def cumulative_standard_normal(z: float) -> float:
    """Return the cumulative distribution value for a standard normal variable."""

    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def sample_mean_std(values: Sequence[float]) -> Tuple[float, float]:
    """Compute the mean and sample standard deviation for ``values``."""

    cleaned = _coerce_finite(values)
    if not cleaned:
        return 0.0, 0.0
    mean = sum(cleaned) / float(len(cleaned))
    if len(cleaned) == 1:
        return mean, 0.0
    variance = sum((value - mean) ** 2 for value in cleaned) / float(len(cleaned) - 1)
    return mean, math.sqrt(variance)


def mean_confidence_interval(
    values: Sequence[float], confidence: float = 0.95
) -> Tuple[float, float]:
    """Compute a symmetric confidence interval for ``values`` using z-scores."""

    cleaned = _coerce_finite(values)
    if not cleaned:
        return 0.0, 0.0
    mean, std = sample_mean_std(cleaned)
    if std == 0.0:
        return mean, mean
    z = inverse_standard_normal((1.0 + confidence) / 2.0)
    margin = z * std / math.sqrt(len(cleaned))
    return mean - margin, mean + margin


def percentile(values: Iterable[float], q: float) -> float:
    """Return the ``q`` percentile (0-100 inclusive) from ``values``."""

    clamped_q = min(max(q, 0.0), 100.0)
    sorted_values: List[float] = sorted(_coerce_finite(values))
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (clamped_q / 100.0) * (len(sorted_values) - 1)
    lower = int(math.floor(rank))
    upper = int(math.ceil(rank))
    if lower == upper:
        return sorted_values[lower]
    weight = rank - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def inverse_standard_normal(p: float) -> float:
    """Approximate inverse CDF for the standard normal distribution."""

    # Beasley-Springer-Moro approximation for inverse Phi.
    if p <= 0 or p >= 1:
        raise ValueError("p must be within (0, 1) exclusive")
    a = [2.50662823884, -18.61500062529, 41.39119773534, -25.44106049637]
    b = [-8.47351093090, 23.08336743743, -21.06224101826, 3.13082909833]
    c = [
        0.3374754822726147,
        0.9761690190917186,
        0.1607979714918209,
        0.0276438810333863,
        0.0038405729373609,
        0.0003951896511919,
        0.0000321767881768,
        0.0000002888167364,
        0.0000003960315187,
    ]
    x = p - 0.5
    if abs(x) < 0.42:
        r = x * x
        numerator = x * (((a[3] * r + a[2]) * r + a[1]) * r + a[0])
        denominator = (((b[3] * r + b[2]) * r + b[1]) * r + b[0]) * r + 1.0
        return numerator / denominator
    r = p if x > 0 else 1.0 - p
    s = math.log(-math.log(r))
    result = c[0] + s * (
        c[1]
        + s * (c[2] + s * (c[3] + s * (c[4] + s * (c[5] + s * (c[6] + s * (c[7] + s * c[8]))))))
    )
    return result if x > 0 else -result


def clamp_probability(probability: float, eps: float = 1e-15) -> float:
    """Return ``probability`` constrained to ``[eps, 1-eps]`` with NaNs mapped to 0.5."""

    try:
        value = float(probability)
    except (TypeError, ValueError):
        return 0.5
    if math.isnan(value):
        return 0.5
    return max(min(value, 1.0 - eps), eps)


def bootstrap_confidence_interval(
    values: Sequence[float],
    *,
    confidence: float = 0.95,
    iterations: int = 1000,
    random_state: Optional[int] = None,
) -> Tuple[float, float]:
    """Return a bootstrap confidence interval for the mean of ``values``."""

    cleaned = _coerce_finite(values)
    if not cleaned:
        return 0.0, 0.0
    if len(cleaned) == 1:
        single = cleaned[0]
        return single, single
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie within (0, 1)")
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    rng = np.random.default_rng(random_state)
    array = np.asarray(cleaned, dtype=float)
    means = np.empty(iterations, dtype=float)
    for index in range(iterations):
        sample = rng.choice(array, size=array.size, replace=True)
        means[index] = float(np.mean(sample))
    lower_q = (1.0 - confidence) / 2.0 * 100.0
    upper_q = (1.0 + confidence) / 2.0 * 100.0
    return float(np.percentile(means, lower_q)), float(np.percentile(means, upper_q))


# === Error & Edge Case Handling ===
# - Numerical operations ignore non-finite values to avoid propagating NaNs.
# - Percentile, bootstrap, and confidence interval routines validate input ranges.
# - Bootstrap sampling falls back to a degenerate interval when only one sample exists.


# === Performance Considerations ===
# - Bootstrap sampling leverages NumPy vectorisation for efficiency.
# - Other operations are O(n) in the number of samples.


# === Exports / Public API ===
__all__ = [
    "bootstrap_confidence_interval",
    "clamp_probability",
    "cumulative_standard_normal",
    "inverse_standard_normal",
    "mean_confidence_interval",
    "percentile",
    "sample_mean_std",
]
