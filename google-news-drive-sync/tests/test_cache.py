from datetime import datetime, timedelta, timezone

from src.cache import ArticleCache
from src.news_fetcher import NewsArticle


def make_article(url: str, title: str, *, published_at: datetime | None = None) -> NewsArticle:
    return NewsArticle(
        title=title,
        description=None,
        url=url,
        published_at=published_at,
        source="Test",
    )


def test_cache_filters_duplicates(tmp_path):
    cache = ArticleCache(tmp_path / "articles.db", retention_days=7)
    article_a = make_article("https://example.com/a", "A")
    article_b = make_article("https://example.com/b", "B")

    fresh = cache.filter_new([article_a, article_b])
    assert fresh == [article_a, article_b]

    cache.record(fresh)
    assert cache.filter_new([article_a]) == []


def test_cache_prunes_expired_entries(tmp_path):
    cache = ArticleCache(tmp_path / "articles.db", retention_days=0)
    old = make_article(
        "https://example.com/old",
        "Old",
        published_at=datetime.now(timezone.utc) - timedelta(days=2),
    )
    cache.record([old])
    cache.record([])  # trigger retention cleanup

    fresh = cache.filter_new([old])
    assert fresh == [old]
