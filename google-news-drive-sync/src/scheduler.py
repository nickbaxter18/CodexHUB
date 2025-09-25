"""Simple scheduler for recurring synchronisation."""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable

logger = logging.getLogger(__name__)


def schedule(
    job: Callable[[], None],
    interval_minutes: int,
) -> threading.Thread:
    """Run *job* every ``interval_minutes`` minutes in a background thread."""

    if interval_minutes <= 0:
        message = "Interval must be greater than zero minutes."
        raise ValueError(message)

    stop_event = threading.Event()

    def worker() -> None:
        logger.info("Starting scheduled job every %s minutes", interval_minutes)
        while not stop_event.is_set():
            start = time.time()
            try:
                job()
            except Exception:  # pragma: no cover - log unexpected issues
                logger.exception("Scheduled job failed")
            elapsed = time.time() - start
            sleep_for = max(0.0, interval_minutes * 60 - elapsed)
            if stop_event.wait(timeout=sleep_for):
                break
        logger.info("Scheduler thread exiting")

    thread = threading.Thread(
        target=worker,
        name="news-sync-scheduler",
        daemon=True,
    )
    thread.stop_event = stop_event  # type: ignore[attr-defined]
    thread.start()
    return thread
