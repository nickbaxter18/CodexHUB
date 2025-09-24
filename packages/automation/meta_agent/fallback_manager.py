"""Fallback macro coordination for resilience testing."""

# === Imports / Dependencies ===
from __future__ import annotations

from typing import Callable, Dict, Mapping, Optional

# === Types, Interfaces, Contracts, Schema ===
FallbackCallable = Callable[[float, float], None]


class FallbackManager:
    """Manage fallback macro invocations when primary macros fail thresholds."""

    def __init__(self, fallbacks: Optional[Mapping[str, object]] = None) -> None:
        self._metric_to_macro: Dict[str, str] = {}
        self._macro_callbacks: Dict[str, FallbackCallable] = {}
        self._metric_callbacks: Dict[str, FallbackCallable] = {}
        if fallbacks:
            for metric, handler in fallbacks.items():
                if callable(handler):
                    self._metric_callbacks[str(metric)] = handler  # backwards compatibility
                else:
                    self._metric_to_macro[str(metric)] = str(handler)

    def register_macro(self, macro_id: str, callback: FallbackCallable) -> None:
        """Register a fallback macro callback by identifier."""

        self._macro_callbacks[macro_id] = callback

    def register_metric_callback(self, metric: str, callback: FallbackCallable) -> None:
        """Register a direct fallback callback for ``metric``."""

        self._metric_callbacks[metric] = callback

    def evaluate_and_trigger(self, metric: str, value: float, threshold: float) -> None:
        """Invoke fallback for ``metric`` if ``value`` breaches ``threshold``."""

        if metric is None or value is None or threshold is None:
            return
        if value <= threshold:
            return
        callback = self._metric_callbacks.get(metric)
        if callback is None:
            macro_id = self._metric_to_macro.get(metric)
            if macro_id:
                callback = self._macro_callbacks.get(macro_id)
        if callback:
            callback(value, threshold)


# === Error & Edge Case Handling ===
# Metrics without configured fallbacks are ignored. None values skip evaluation.


# === Performance / Resource Considerations ===
# Operations are O(1) dictionary lookups; fallbacks defer to user-supplied callables.


# === Exports / Public API ===
__all__ = ["FallbackManager", "FallbackCallable"]
