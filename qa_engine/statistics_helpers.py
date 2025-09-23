"""Statistical helper routines supporting probabilistic QA decisions."""

# === Header & Purpose ===
# Encapsulates statistical utilities shared across probabilistic QA analyses,
# including cumulative distributions, percentile computation, and confidence
# interval estimation for sample observations.

# === Imports / Dependencies ===
from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple


def cumulative_standard_normal(z: float) -> float:
    """Return the cumulative distribution value for a standard normal variable."""

    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def sample_mean_std(values: Sequence[float]) -> Tuple[float, float]:
    """Compute the mean and sample standard deviation for ``values``."""

    if not values:
        return 0.0, 0.0
    mean = sum(values) / float(len(values))
    if len(values) == 1:
        return mean, 0.0
    variance = sum((value - mean) ** 2 for value in values) / float(len(values) - 1)
    return mean, math.sqrt(variance)


def mean_confidence_interval(
    values: Sequence[float], confidence: float = 0.95
) -> Tuple[float, float]:
    """Compute a symmetric confidence interval for ``values`` using z-scores."""

    if not values:
        return 0.0, 0.0
    mean, std = sample_mean_std(values)
    if std == 0.0:
        return mean, mean
    z = inverse_standard_normal((1.0 + confidence) / 2.0)
    margin = z * std / math.sqrt(len(values))
    return mean - margin, mean + margin


def percentile(values: Iterable[float], q: float) -> float:
    """Return the ``q`` percentile (0-100 inclusive) from ``values``."""

    clamped_q = min(max(q, 0.0), 100.0)
    sorted_values: List[float] = sorted(values)
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


# === Error & Edge Case Handling ===
# - Percentile and confidence interval routines handle empty inputs gracefully.
# - Inverse CDF rejects boundary probabilities to avoid infinities.


# === Performance Considerations ===
# - Operations are vector-free and suitable for tight loops. Complexity is O(n) for
#   percentile and mean calculations.


# === Exports / Public API ===
__all__ = [
    "cumulative_standard_normal",
    "inverse_standard_normal",
    "mean_confidence_interval",
    "percentile",
    "sample_mean_std",
]
