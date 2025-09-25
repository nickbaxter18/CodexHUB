"""Persistence layer for storing aggregated articles."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from .news_fetcher import NewsArticle
from .utils import utcnow


@dataclass(frozen=True)
class ArticleRecord:
    """Serializable representation of an article stored in SQLite."""

    id: str
    title: str
    description: str | None
    url: str
    source: str | None
    published_at: datetime | None

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at.isoformat()
            if isinstance(self.published_at, datetime)
            else None,
        }


class ArticleRepository:
    """Store article metadata for the dashboard and API."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
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
                CREATE TABLE IF NOT EXISTS article_records (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    url TEXT NOT NULL,
                    source TEXT,
                    published_at TEXT,
                    inserted_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _article_id(self, article: NewsArticle) -> str:
        return article.url or article.title

    def persist(self, articles: Iterable[NewsArticle]) -> None:
        now = utcnow().isoformat()
        payload: List[tuple[str, str, str | None, str, str | None, str | None, str]] = []
        for article in articles:
            identifier = self._article_id(article)
            if not identifier:
                continue
            published = None
            if article.published_at is not None:
                published_dt = article.published_at
                if published_dt.tzinfo is None:
                    published_dt = published_dt.replace(tzinfo=timezone.utc)
                else:
                    published_dt = published_dt.astimezone(timezone.utc)
                published = published_dt.isoformat()
            payload.append(
                (
                    identifier,
                    article.title,
                    article.description,
                    article.url,
                    article.source,
                    published,
                    now,
                )
            )

        if not payload:
            return

        with self._connect() as conn:
            conn.executemany(
                (
                    "INSERT OR REPLACE INTO article_records "
                    "(id, title, description, url, source, "
                    "published_at, inserted_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
                ),
                payload,
            )
            conn.commit()

    def list_articles(
        self,
        *,
        limit: Optional[int] = None,
        source: str | None = None,
        query: str | None = None,
    ) -> List[ArticleRecord]:
        clauses: List[str] = []
        params: List[object] = []

        if source:
            clauses.append("source = ?")
            params.append(source)
        if query:
            like = f"%{query.lower()}%"
            clauses.append("(lower(title) LIKE ? OR lower(description) LIKE ?)")
            params.extend([like, like])

        statement = [
            "SELECT id, title, description, url, source, published_at",
            "FROM article_records",
        ]
        if clauses:
            statement.append("WHERE " + " AND ".join(clauses))
        statement.append("ORDER BY COALESCE(published_at, inserted_at) DESC")
        if limit:
            statement.append("LIMIT ?")
            params.append(limit)

        query_str = " ".join(statement)
        with self._connect() as conn:
            rows = conn.execute(query_str, params).fetchall()

        results: List[ArticleRecord] = []
        for row in rows:
            published = None
            if row[5]:
                published = datetime.fromisoformat(row[5])
            results.append(
                ArticleRecord(
                    id=row[0],
                    title=row[1],
                    description=row[2],
                    url=row[3],
                    source=row[4],
                    published_at=published,
                )
            )
        return results

    def list_sources(self) -> List[str]:
        with self._connect() as conn:
            rows = conn.execute(
                (
                    "SELECT DISTINCT source FROM article_records "
                    "WHERE source IS NOT NULL ORDER BY source"
                )
            ).fetchall()
        return [row[0] for row in rows if row[0]]

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM article_records").fetchone()
        return int(row[0]) if row else 0

    def latest_published(self) -> datetime | None:
        with self._connect() as conn:
            row = conn.execute(
                ("SELECT published_at FROM article_records " "ORDER BY published_at DESC LIMIT 1")
            ).fetchone()
        if not row or row[0] is None:
            return None
        return datetime.fromisoformat(row[0])


__all__ = ["ArticleRecord", "ArticleRepository"]
