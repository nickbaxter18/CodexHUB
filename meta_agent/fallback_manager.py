"""Fallback macro coordination for resilience testing."""

# === Imports / Dependencies ===
from __future__ import annotations

from typing import Callable, Dict


# === Types, Interfaces, Contracts, Schema ===
FallbackCallable = Callable[[float, float], None]


class FallbackManager:
    """Manage fallback macro invocations when primary macros fail thresholds."""

    def __init__(self, fallbacks: Dict[str, FallbackCallable]) -> None:
        self.fallbacks = dict(fallbacks)

    def evaluate_and_trigger(self, metric: str, value: float, threshold: float) -> None:
        """Invoke fallback for ``metric`` if ``value`` breaches ``threshold``."""

        if metric in self.fallbacks and value is not None and threshold is not None:
            if value > threshold:
                self.fallbacks[metric](value, threshold)


# === Error & Edge Case Handling ===
# Metrics without configured fallbacks are ignored. None values skip evaluation.


# === Performance / Resource Considerations ===
# Operations are O(1) dictionary lookups; fallbacks defer to user-supplied callables.


# === Exports / Public API ===
__all__ = ["FallbackManager", "FallbackCallable"]
