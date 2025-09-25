"""Monitoring utilities for the sync pipeline."""

from __future__ import annotations

import logging
from collections import Counter, defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean
from threading import Lock
from time import perf_counter
from typing import ContextManager, Dict, Iterator, List, Optional

from .utils import utcnow

logger = logging.getLogger(__name__)


@dataclass
class MonitoringSnapshot:
    """Serializable snapshot of collected metrics."""

    articles_processed: int = 0
    errors: int = 0
    source_counts: Dict[str, int] = field(default_factory=dict)
    documents_uploaded: int = 0
    runs: int = 0
    last_run_started: Optional[datetime] = None
    last_run_completed: Optional[datetime] = None
    last_status: str = "idle"
    latency: Dict[str, Dict[str, float]] = field(default_factory=dict)
    queue_depth: Dict[str, float] = field(default_factory=dict)


class MonitoringClient:
    """Collect lightweight metrics during pipeline execution."""

    def __init__(self) -> None:
        self._articles_processed = 0
        self._errors = 0
        self._sources: Counter[str] = Counter()
        self._documents_uploaded = 0
        self._runs = 0
        self._last_run_started: datetime | None = None
        self._last_run_completed: datetime | None = None
        self._last_status: str = "idle"
        self._latencies: Dict[str, List[float]] = defaultdict(list)
        self._queue_samples: deque[int] = deque(maxlen=50)
        self._lock = Lock()

    def record_articles(self, source: str, count: int) -> None:
        with self._lock:
            self._articles_processed += count
            self._sources[source] += count
        logger.debug("Recorded %s articles from %s", count, source)

    def record_error(self, source: str, error: Exception) -> None:
        with self._lock:
            self._errors += 1
        logger.error("Error in source %s: %s", source, error)

    def start_run(self) -> None:
        with self._lock:
            self._last_run_started = utcnow()
            self._last_status = "running"

    def complete_run(self, *, status: str = "success") -> None:
        with self._lock:
            self._runs += 1
            self._last_run_completed = utcnow()
            self._last_status = status

    def record_document_upload(self) -> None:
        with self._lock:
            self._documents_uploaded += 1

    def record_latency(self, label: str, seconds: float) -> None:
        if seconds < 0:
            return
        with self._lock:
            self._latencies[label].append(seconds)

    def track_latency(self, label: str) -> ContextManager[None]:
        """Context manager that records elapsed time under *label*."""

        @contextmanager
        def _tracker() -> Iterator[None]:
            start = perf_counter()
            try:
                yield
            finally:
                self.record_latency(label, perf_counter() - start)

        return _tracker()

    def record_queue_depth(self, depth: int) -> None:
        if depth < 0:
            return
        with self._lock:
            self._queue_samples.append(depth)

    def snapshot(self) -> MonitoringSnapshot:
        latency_stats = {
            label: {
                "count": float(len(samples)),
                "avg": float(mean(samples)) if samples else 0.0,
                "p95": float(_percentile(samples, 0.95)),
            }
            for label, samples in self._latencies.items()
        }
        queue_depth: Dict[str, float] = {}
        if self._queue_samples:
            samples = list(self._queue_samples)
            queue_depth = {
                "latest": float(samples[-1]),
                "max": float(max(samples)),
                "avg": float(mean(samples)),
            }

        return MonitoringSnapshot(
            articles_processed=self._articles_processed,
            errors=self._errors,
            source_counts=dict(self._sources),
            documents_uploaded=self._documents_uploaded,
            runs=self._runs,
            last_run_started=self._last_run_started,
            last_run_completed=self._last_run_completed,
            last_status=self._last_status,
            latency=latency_stats,
            queue_depth=queue_depth,
        )

    def emit(self) -> None:
        snap = self.snapshot()
        logger.info(
            "Metrics - articles: %s, errors: %s, sources: %s, latency: %s",
            snap.articles_processed,
            snap.errors,
            snap.source_counts,
            snap.latency,
        )

    def metrics(self) -> Dict[str, object]:
        snap = self.snapshot()
        return {
            "articles_processed": snap.articles_processed,
            "errors": snap.errors,
            "documents_uploaded": snap.documents_uploaded,
            "runs": snap.runs,
            "last_run_started": snap.last_run_started.isoformat()
            if snap.last_run_started
            else None,
            "last_run_completed": snap.last_run_completed.isoformat()
            if snap.last_run_completed
            else None,
            "last_status": snap.last_status,
            "source_counts": snap.source_counts,
            "latency": snap.latency,
            "queue_depth": snap.queue_depth,
        }

    def render_prometheus(self) -> str:
        snap = self.snapshot()
        lines = [
            "# TYPE gnds_articles_processed_total counter",
            f"gnds_articles_processed_total {snap.articles_processed}",
            "# TYPE gnds_errors_total counter",
            f"gnds_errors_total {snap.errors}",
            "# TYPE gnds_documents_uploaded_total counter",
            f"gnds_documents_uploaded_total {snap.documents_uploaded}",
            "# TYPE gnds_runs_total counter",
            f"gnds_runs_total {snap.runs}",
        ]
        for source, count in snap.source_counts.items():
            lines.append(f'gnds_source_articles_total{{source="{source}"}} {count}')
        if snap.last_run_started:
            lines.append(
                ("gnds_last_run_started_timestamp " f"{snap.last_run_started.timestamp()}")
            )
        if snap.last_run_completed:
            lines.append(
                ("gnds_last_run_completed_timestamp " f"{snap.last_run_completed.timestamp()}")
            )
        lines.append(f'gnds_last_status{{status="{snap.last_status}"}} 1')
        for label, stats in snap.latency.items():
            total = stats.get("avg", 0.0) * stats.get("count", 0.0)
            count = int(stats.get("count", 0))
            lines.append(f'gnds_latency_seconds_sum{{stage="{label}"}} {total}')
            lines.append(f'gnds_latency_seconds_count{{stage="{label}"}} {count}')
            p95 = stats.get("p95", 0.0)
            lines.append(f'gnds_latency_seconds_p95{{stage="{label}"}} {p95}')
        if snap.queue_depth:
            lines.append(f"gnds_repository_queue_depth {snap.queue_depth.get('latest', 0.0)}")
            lines.append(f"gnds_repository_queue_depth_max {snap.queue_depth.get('max', 0.0)}")
        return "\n".join(lines)


def _percentile(samples: List[float], percentile: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    index = max(0, min(len(ordered) - 1, int(round(percentile * (len(ordered) - 1)))))
    return ordered[index]


__all__ = ["MonitoringClient", "MonitoringSnapshot"]
