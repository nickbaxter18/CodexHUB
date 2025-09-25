"""Lightweight caching utilities to avoid duplicate uploads."""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Iterator, List

from .news_fetcher import NewsArticle


class ArticleCache:
    """Store seen article identifiers in a SQLite database."""

    def __init__(self, path: str | Path, *, retention_days: int = 7) -> None:
        self.path = Path(path)
        self.retention_days = retention_days
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialise()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        try:
            yield connection
        finally:
            connection.close()

    def _initialise(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    published_at TEXT
                )
                """
            )
            conn.commit()

    def _article_key(self, article: NewsArticle) -> str:
        data = article.url or article.title
        digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
        return digest

    def filter_new(self, articles: Iterable[NewsArticle]) -> List[NewsArticle]:
        fresh: List[NewsArticle] = []
        with self._connect() as conn:
            for article in articles:
                if not article.url and not article.title:
                    continue
                key = self._article_key(article)
                cursor = conn.execute(
                    "SELECT 1 FROM articles WHERE id = ?",
                    (key,),
                )
                if cursor.fetchone():
                    continue
                fresh.append(article)
        return fresh

    def record(self, articles: Iterable[NewsArticle]) -> None:
        now = datetime.utcnow()
        cutoff = now - timedelta(days=self.retention_days)
        with self._connect() as conn:
            conn.executemany(
                ("INSERT OR REPLACE INTO articles " "(id, url, published_at) VALUES (?, ?, ?)"),
                [
                    (
                        self._article_key(article),
                        article.url or article.title,
                        (article.published_at or now).isoformat(),
                    )
                    for article in articles
                ],
            )
            conn.execute(
                "DELETE FROM articles WHERE published_at < ?",
                (cutoff.isoformat(),),
            )
            conn.commit()


__all__ = ["ArticleCache"]
