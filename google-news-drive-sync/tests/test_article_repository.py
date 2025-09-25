from datetime import datetime

from src.article_repository import ArticleRepository
from src.news_fetcher import NewsArticle


def make_article(index: int) -> NewsArticle:
    return NewsArticle(
        title=f"Article {index}",
        description=f"Description {index}",
        url=f"https://example.com/{index}",
        published_at=datetime(2024, 1, index + 1),
        source="Example",
    )


def test_persist_and_list_articles(tmp_path):
    repo = ArticleRepository(tmp_path / "articles.db")

    articles = [make_article(1), make_article(2)]
    repo.persist(articles)

    stored = repo.list_articles()
    assert len(stored) == 2
    assert stored[0].title.startswith("Article")


def test_filtering_and_counts(tmp_path):
    repo = ArticleRepository(tmp_path / "articles.db")
    repo.persist([make_article(1), make_article(2)])

    filtered = repo.list_articles(query="article 1")
    assert len(filtered) == 1

    assert repo.count() == 2
    assert repo.list_sources() == ["Example"]
