"""Google News Drive Sync package exports."""

from .main import main
from .news_fetcher import NewsArticle, fetch_news

__all__ = [
    "main",
    "NewsArticle",
    "fetch_news",
]
