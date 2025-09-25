"""FastAPI application exposing aggregated news data with optional security."""
# ruff: noqa: B008  # FastAPI dependencies rely on Depends defaults

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Sequence

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Security
from fastapi.responses import PlainTextResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from .article_repository import ArticleRepository
from .monitor import MonitoringClient

logger = logging.getLogger(__name__)


class RateLimiter:
    """In-memory rate limiter implementing a rolling time window."""

    def __init__(self, limit: int, *, window_seconds: float = 60.0) -> None:
        if limit <= 0:
            raise ValueError("limit must be greater than zero")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be greater than zero")
        self.limit = int(limit)
        self.window = float(window_seconds)
        self._events: Dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, identity: str) -> None:
        """Record an access for *identity*, raising on limit exhaustion."""

        if not identity:
            identity = "anonymous"

        now = time.monotonic()
        with self._lock:
            events = self._events.setdefault(identity, deque())
            while events and now - events[0] > self.window:
                events.popleft()
            if len(events) >= self.limit:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            events.append(now)


class ArticleResponse(BaseModel):
    """Response model for a single article."""

    id: str
    title: str
    description: Optional[str]
    url: str
    source: Optional[str]
    published_at: Optional[str]


class StatusResponse(BaseModel):
    """Expose pipeline status and metrics."""

    metrics: Dict[str, Any]


def _get_repository(repo: ArticleRepository | None) -> ArticleRepository:
    if repo is None:
        raise HTTPException(
            status_code=503,
            detail="Article repository unavailable",
        )
    return repo


def create_app(
    *,
    repository: ArticleRepository | None,
    monitor: MonitoringClient | None,
    api_keys: Sequence[str] | None = None,
    rate_limiter: RateLimiter | None = None,
) -> FastAPI:
    """Create a FastAPI application bound to the provided dependencies."""

    app = FastAPI(title="Google News Drive Sync Dashboard")

    def get_repository() -> ArticleRepository:
        return _get_repository(repository)

    def get_monitor() -> MonitoringClient | None:
        return monitor

    api_key_set = {key for key in api_keys or [] if key}
    api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)
    header_name = api_key_scheme.model.name  # type: ignore[attr-defined]

    if api_key_set:

        async def require_api_key(api_key: str = Security(api_key_scheme)) -> str:
            if not api_key or api_key not in api_key_set:
                raise HTTPException(status_code=401, detail="Invalid API key")
            return api_key

    else:

        async def require_api_key() -> str:
            return ""

    def enforce_security(
        request: Request,
        api_key: str = Depends(require_api_key),
    ) -> None:
        identity = api_key
        if not identity:
            client = request.client
            header_value = request.headers.get(header_name)
            if header_value:
                identity = header_value
            else:
                identity = client.host if client else "anonymous"
        if rate_limiter is not None:
            rate_limiter.hit(identity)

    security_dependencies = []
    if api_key_set or rate_limiter is not None:
        security_dependencies = [Depends(enforce_security)]

    @app.get("/health")
    def healthcheck() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get(
        "/articles",
        response_model=List[ArticleResponse],
        dependencies=security_dependencies,
    )
    def list_articles(
        limit: int = Query(20, ge=1, le=100),
        source: Optional[str] = None,
        q: Optional[str] = Query(
            default=None,
            description="Search query",
        ),
        repo: ArticleRepository = Depends(get_repository),
    ) -> List[ArticleResponse]:
        records = repo.list_articles(limit=limit, source=source, query=q)
        return [
            ArticleResponse(
                id=item.id,
                title=item.title,
                description=item.description,
                url=item.url,
                source=item.source,
                published_at=item.published_at.isoformat() if item.published_at else None,
            )
            for item in records
        ]

    @app.get("/sources", dependencies=security_dependencies)
    def sources(
        repo: ArticleRepository = Depends(get_repository),
    ) -> Dict[str, List[str]]:
        return {"sources": repo.list_sources()}

    @app.get(
        "/status",
        response_model=StatusResponse,
        dependencies=security_dependencies,
    )
    def status(
        repo: ArticleRepository = Depends(get_repository),
        metrics_client: MonitoringClient | None = Depends(get_monitor),
    ) -> StatusResponse:
        metrics: Dict[str, Any] = {
            "articles": repo.count(),
            "sources": repo.list_sources(),
        }
        if metrics_client is not None:
            metrics.update(metrics_client.metrics())
        return StatusResponse(metrics=metrics)

    @app.get(
        "/metrics",
        response_class=PlainTextResponse,
        dependencies=security_dependencies,
    )
    def metrics_endpoint(
        metrics_client: MonitoringClient | None = Depends(get_monitor),
    ) -> PlainTextResponse:
        if metrics_client is None:
            return PlainTextResponse("", media_type="text/plain")
        payload = metrics_client.render_prometheus()
        return PlainTextResponse(payload, media_type="text/plain")

    return app


def run_server(app: FastAPI, *, host: str, port: int) -> None:
    """Run a uvicorn server for *app*."""

    try:
        import uvicorn
    except ImportError as exc:
        # pragma: no cover - dependency missing at runtime
        raise RuntimeError("uvicorn must be installed to serve the API") from exc

    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    logger.info("Starting dashboard server on %s:%s", host, port)
    server.run()


__all__ = [
    "create_app",
    "run_server",
    "ArticleResponse",
    "StatusResponse",
    "RateLimiter",
]
