"""Scheduling utilities built on top of APScheduler."""

from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

try:  # pragma: no cover - dependency optional during tests
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception:  # pragma: no cover - fallback to thread-based scheduler
    BackgroundScheduler = None  # type: ignore[assignment]


@dataclass
class SchedulerHandle:
    """Represents a scheduled job and allows graceful shutdown."""

    scheduler: Any | None = None
    job_id: str | None = None
    thread: threading.Thread | None = None

    def shutdown(self) -> None:
        if self.scheduler is not None:
            try:
                if self.job_id:
                    self.scheduler.remove_job(self.job_id)
            finally:
                self.scheduler.shutdown(wait=False)
        if self.thread is not None:
            stop_event = getattr(self.thread, "stop_event", None)
            if stop_event is not None:
                stop_event.set()
            self.thread.join(timeout=1)


def _start_thread(
    job: Callable[[], None],
    interval_minutes: int,
) -> threading.Thread:
    stop_event = threading.Event()

    def worker() -> None:
        logger.info(
            "Starting fallback scheduler every %s minutes",
            interval_minutes,
        )
        while not stop_event.is_set():
            start = time.time()
            try:
                job()
            except Exception:  # pragma: no cover - best-effort logging
                logger.exception("Scheduled job failed")
            elapsed = time.time() - start
            sleep_for = max(0.0, interval_minutes * 60 - elapsed)
            if stop_event.wait(timeout=sleep_for):
                break
        logger.info("Fallback scheduler thread exiting")

    thread = threading.Thread(
        target=worker,
        name="news-sync-scheduler",
        daemon=True,
    )
    thread.stop_event = stop_event  # type: ignore[attr-defined]
    thread.start()
    return thread


def _create_scheduler(timezone: str | None) -> Any | None:
    if BackgroundScheduler is None:  # pragma: no cover
        return None
    options: Dict[str, Any] = {}
    if timezone:
        options["timezone"] = timezone
    return BackgroundScheduler(**options)


def schedule(
    job: Callable[[], None],
    *,
    interval_minutes: Optional[int] = None,
    cron: Optional[Dict[str, Any]] = None,
    scheduler: Any | None = None,
    timezone: str | None = None,
) -> SchedulerHandle:
    """Schedule *job* using APScheduler when available.

    When APScheduler is unavailable the function falls back to the
    previous thread-based scheduler.
    """

    if scheduler is None:
        scheduler = _create_scheduler(timezone)

    if scheduler is not None:
        trigger_kwargs: Dict[str, Any]
        trigger: str
        if cron:
            trigger = "cron"
            trigger_kwargs = dict(cron)
        else:
            if interval_minutes is None or interval_minutes <= 0:
                raise ValueError("interval_minutes must be provided when cron is not set")
            trigger = "interval"
            trigger_kwargs = {"minutes": interval_minutes}

        job_id = f"news-sync-{uuid.uuid4()}"
        scheduler.add_job(
            job,
            trigger,
            id=job_id,
            max_instances=1,
            coalesce=True,
            replace_existing=True,
            **trigger_kwargs,
        )
        scheduler.start()
        logger.info(
            "Scheduled job using APScheduler with trigger %s",
            trigger,
        )
        return SchedulerHandle(scheduler=scheduler, job_id=job_id)

    if interval_minutes is None or interval_minutes <= 0:
        raise ValueError(
            ("interval_minutes must be greater than zero when using " "fallback scheduler")
        )

    thread = _start_thread(job, interval_minutes)
    return SchedulerHandle(thread=thread)
