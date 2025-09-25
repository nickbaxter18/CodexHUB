from datetime import datetime

from fastapi.testclient import TestClient

from src.article_repository import ArticleRepository
from src.monitor import MonitoringClient
from src.news_fetcher import NewsArticle
from src.server import RateLimiter, create_app


def populate(repo: ArticleRepository) -> None:
    repo.persist(
        [
            NewsArticle(
                title="Title",
                description="Desc",
                url="https://example.com/1",
                published_at=datetime(2024, 1, 1),
                source="SourceA",
            )
        ]
    )


def test_articles_endpoint(tmp_path):
    repo = ArticleRepository(tmp_path / "articles.db")
    populate(repo)
    monitor = MonitoringClient()
    monitor.record_articles("news_api", 1)
    monitor.record_document_upload()
    monitor.complete_run(status="success")

    app = create_app(
        repository=repo,
        monitor=monitor,
        api_keys=["secret"],
        rate_limiter=RateLimiter(limit=5, window_seconds=60),
    )
    client = TestClient(app)
    headers = {"X-API-Key": "secret"}

    response = client.get("/articles", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data[0]["title"] == "Title"

    sources = client.get("/sources", headers=headers).json()
    assert sources["sources"] == ["SourceA"]

    status = client.get("/status", headers=headers).json()
    assert status["metrics"]["articles"] == 1

    metrics = client.get("/metrics", headers=headers)
    assert "gnds_articles_processed_total" in metrics.text

    unauthorised = client.get("/articles")
    assert unauthorised.status_code == 401


def test_rate_limit_is_enforced(tmp_path):
    repo = ArticleRepository(tmp_path / "articles.db")
    populate(repo)
    limiter = RateLimiter(limit=1, window_seconds=60)
    app = create_app(
        repository=repo,
        monitor=None,
        api_keys=["secret"],
        rate_limiter=limiter,
    )
    client = TestClient(app)
    headers = {"X-API-Key": "secret"}

    first = client.get("/articles", headers=headers)
    assert first.status_code == 200
    second = client.get("/articles", headers=headers)
    assert second.status_code == 429


def test_healthcheck_without_monitor(tmp_path):
    repo = ArticleRepository(tmp_path / "articles.db")
    populate(repo)

    app = create_app(repository=repo, monitor=None)
    client = TestClient(app)

    assert client.get("/health").json() == {"status": "ok"}
