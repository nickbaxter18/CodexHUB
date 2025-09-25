"""Monitoring utilities for the sync pipeline."""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

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

    def record_articles(self, source: str, count: int) -> None:
        self._articles_processed += count
        self._sources[source] += count
        logger.debug("Recorded %s articles from %s", count, source)

    def record_error(self, source: str, error: Exception) -> None:
        self._errors += 1
        logger.error("Error in source %s: %s", source, error)

    def start_run(self) -> None:
        self._last_run_started = datetime.utcnow()
        self._last_status = "running"

    def complete_run(self, *, status: str = "success") -> None:
        self._runs += 1
        self._last_run_completed = datetime.utcnow()
        self._last_status = status

    def record_document_upload(self) -> None:
        self._documents_uploaded += 1

    def snapshot(self) -> MonitoringSnapshot:
        return MonitoringSnapshot(
            articles_processed=self._articles_processed,
            errors=self._errors,
            source_counts=dict(self._sources),
            documents_uploaded=self._documents_uploaded,
            runs=self._runs,
            last_run_started=self._last_run_started,
            last_run_completed=self._last_run_completed,
            last_status=self._last_status,
        )

    def emit(self) -> None:
        snap = self.snapshot()
        logger.info(
            "Metrics - articles: %s, errors: %s, sources: %s",
            snap.articles_processed,
            snap.errors,
            snap.source_counts,
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
        return "\n".join(lines)


__all__ = ["MonitoringClient", "MonitoringSnapshot"]
