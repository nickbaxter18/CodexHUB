"""
SECTION: Header & Purpose
    - Provides a lightweight thread-safe publish/subscribe event bus dedicated to QA signals.
    - Enables decoupled communication between agents, orchestrators, and arbitration components.

SECTION: Imports / Dependencies
    - Uses Python's standard ``threading`` primitives and typing utilities only.
"""
from __future__ import annotations

import logging
import threading
from collections import defaultdict
from typing import Any, Callable, DefaultDict, List


EventCallback = Callable[[str, Any], None]


class QAEventBus:
    """Thread-safe event bus dedicated to QA telemetry and arbitration events."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[EventCallback]] = defaultdict(list)
        self._lock = threading.RLock()
        logging.debug("QAEventBus initialised")

    def subscribe(self, event_type: str, callback: EventCallback) -> None:
        """Register ``callback`` to receive events of type ``event_type``."""

        with self._lock:
            self._subscribers[event_type].append(callback)
            logging.debug("QAEventBus subscriber added for '%s': %s", event_type, callback)

    def unsubscribe(self, event_type: str, callback: EventCallback) -> None:
        """Remove ``callback`` from the subscription list for ``event_type`` if present."""

        with self._lock:
            callbacks = self._subscribers.get(event_type, [])
            if callback in callbacks:
                callbacks.remove(callback)
                logging.debug("QAEventBus subscriber removed for '%s': %s", event_type, callback)
            if not callbacks and event_type in self._subscribers:
                del self._subscribers[event_type]

    def publish(self, event_type: str, data: Any) -> None:
        """Publish ``data`` to all subscribers registered under ``event_type``."""

        with self._lock:
            subscribers_snapshot = list(self._subscribers.get(event_type, []))
        logging.debug("QAEventBus publishing '%s' to %d subscriber(s)", event_type, len(subscribers_snapshot))
        for callback in subscribers_snapshot:
            try:
                callback(event_type, data)
            except Exception as exc:  # defensive: prevent one subscriber from blocking others
                logging.exception("QAEventBus subscriber failure for '%s': %s", event_type, exc)

    def clear(self) -> None:
        """Remove all registered subscribers, useful for tear-down in tests."""

        with self._lock:
            self._subscribers.clear()
            logging.debug("QAEventBus cleared")
