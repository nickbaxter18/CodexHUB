"""FastAPI application exposing aggregated news data."""
# ruff: noqa: B008  # FastAPI dependencies rely on Depends defaults

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from .article_repository import ArticleRepository
from .monitor import MonitoringClient

logger = logging.getLogger(__name__)


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
) -> FastAPI:
    """Create a FastAPI application bound to the provided dependencies."""

    app = FastAPI(title="Google News Drive Sync Dashboard")

    def get_repository() -> ArticleRepository:
        return _get_repository(repository)

    def get_monitor() -> MonitoringClient | None:
        return monitor

    @app.get("/health")
    def healthcheck() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/articles", response_model=List[ArticleResponse])
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

    @app.get("/sources")
    def sources(
        repo: ArticleRepository = Depends(get_repository),
    ) -> Dict[str, List[str]]:
        return {"sources": repo.list_sources()}

    @app.get("/status", response_model=StatusResponse)
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

    @app.get("/metrics", response_class=PlainTextResponse)
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


__all__ = ["create_app", "run_server", "ArticleResponse", "StatusResponse"]
