from datetime import datetime

from fastapi.testclient import TestClient

from src.article_repository import ArticleRepository
from src.monitor import MonitoringClient
from src.news_fetcher import NewsArticle
from src.server import create_app


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

    app = create_app(repository=repo, monitor=monitor)
    client = TestClient(app)

    response = client.get("/articles")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["title"] == "Title"

    sources = client.get("/sources").json()
    assert sources["sources"] == ["SourceA"]

    status = client.get("/status").json()
    assert status["metrics"]["articles"] == 1

    metrics = client.get("/metrics")
    assert "gnds_articles_processed_total" in metrics.text


def test_healthcheck_without_monitor(tmp_path):
    repo = ArticleRepository(tmp_path / "articles.db")
    populate(repo)

    app = create_app(repository=repo, monitor=None)
    client = TestClient(app)

    assert client.get("/health").json() == {"status": "ok"}
