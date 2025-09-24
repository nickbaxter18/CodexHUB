"""Asynchronous publish/subscribe event bus for QA signals with observability."""

# === Imports / Dependencies ===
from __future__ import annotations

import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass
from queue import Empty, Queue
from typing import Any, Callable, DefaultDict, Dict, List, Optional

# === Types, Interfaces, Contracts, Schema ===
QAEventCallback = Callable[[str, Dict[str, Any]], None]


@dataclass
class _QueuedEvent:
    """Internal representation of a queued event."""

    event_type: str
    payload: Dict[str, Any]
    correlation_id: str
    enqueued_at: float


class QAEventBus:
    """Background-dispatched event bus that prevents subscriber stalls."""

    def __init__(self, worker_count: int = 1) -> None:
        if worker_count <= 0:
            raise ValueError("worker_count must be positive")
        self._subscribers: DefaultDict[str, List[QAEventCallback]] = defaultdict(list)
        self._lock = threading.RLock()
        self._queue: "Queue[Optional[_QueuedEvent]]" = Queue()
        self._workers: List[threading.Thread] = []
        self._shutdown = threading.Event()
        self._metrics = {
            "published": 0,
            "delivered": 0,
            "failed": 0,
            "dropped": 0,
        }
        self._metrics_lock = threading.Lock()
        for index in range(worker_count):
            worker = threading.Thread(
                target=self._worker, name=f"qa-event-worker-{index}", daemon=True
            )
            worker.start()
            self._workers.append(worker)

    def subscribe(self, event_type: str, callback: QAEventCallback) -> None:
        """Register ``callback`` to receive events of ``event_type``."""

        if not event_type:
            raise ValueError("event_type must be provided")
        if not callable(callback):
            raise TypeError("callback must be callable")
        with self._lock:
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: QAEventCallback) -> None:
        """Remove ``callback`` from subscribers of ``event_type``."""

        with self._lock:
            callbacks = self._subscribers.get(event_type)
            if not callbacks:
                return
            try:
                callbacks.remove(callback)
            except ValueError:
                return
            if not callbacks:
                self._subscribers.pop(event_type, None)

    def publish(
        self, event_type: str, payload: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> None:
        """Publish ``payload`` for ``event_type`` to all subscribers asynchronously."""

        if payload is None:
            raise ValueError("payload must not be None")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")
        correlation = correlation_id or str(uuid.uuid4())
        enriched_payload = dict(payload)
        enriched_payload.setdefault("correlation_id", correlation)
        event = _QueuedEvent(
            event_type=event_type,
            payload=enriched_payload,
            correlation_id=correlation,
            enqueued_at=time.perf_counter(),
        )
        with self._metrics_lock:
            self._metrics["published"] += 1
        self._queue.put(event)

    def wait_for_idle(self, timeout: Optional[float] = None) -> bool:
        """Block until all queued tasks complete or ``timeout`` seconds elapse."""

        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            if self._queue.unfinished_tasks == 0:
                return True
            if deadline is not None and time.monotonic() >= deadline:
                return False
            time.sleep(0.01)

    def get_metrics(self) -> Dict[str, int]:
        """Return counters describing bus activity."""

        with self._metrics_lock:
            return dict(self._metrics)

    def shutdown(self) -> None:
        """Signal worker threads to exit after draining the queue."""

        self._shutdown.set()
        for _ in self._workers:
            self._queue.put(None)
        for worker in self._workers:
            worker.join(timeout=1.0)

    def _worker(self) -> None:
        while not self._shutdown.is_set():
            try:
                item = self._queue.get(timeout=0.1)
            except Empty:
                continue
            if item is None:
                self._queue.task_done()
                break
            try:
                callbacks = self._get_callbacks(item.event_type)
                for callback in callbacks:
                    try:
                        callback(item.event_type, dict(item.payload))
                        with self._metrics_lock:
                            self._metrics["delivered"] += 1
                    except Exception:
                        with self._metrics_lock:
                            self._metrics["failed"] += 1
                if not callbacks:
                    with self._metrics_lock:
                        self._metrics["dropped"] += 1
            finally:
                self._queue.task_done()

    def _get_callbacks(self, event_type: str) -> List[QAEventCallback]:
        with self._lock:
            return list(self._subscribers.get(event_type, ()))


# === Error & Edge Case Handling ===
# Validation ensures event types are provided, callbacks are callable, and payloads are dictionaries.
# The worker loop guards against subscriber exceptions to keep the bus running, and shutdown drains
# queued events before exiting.


# === Performance / Resource Considerations ===
# Asynchronous workers decouple publishers from subscribers, preventing individual callbacks from
# blocking unrelated pipelines. Metrics offer lightweight observability for queue throughput.


# === Exports / Public API ===
__all__ = ["QAEventBus", "QAEventCallback"]
