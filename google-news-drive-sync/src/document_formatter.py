"""Document formatter for news articles."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Tuple

from .news_fetcher import NewsArticle

logger = logging.getLogger(__name__)


def _format_timestamp(timestamp: datetime | None) -> str:
    if timestamp is None:
        return "Unknown"
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def create_document(
    articles: Iterable[NewsArticle],
    *,
    format: str = "markdown",
    timezone_name: str | None = None,
) -> Tuple[str, bytes]:
    """Create a document representation from *articles*.

    Returns a tuple of ``(filename, content_bytes)`` suitable for upload.
    """

    articles_list: List[NewsArticle] = [
        article for article in articles if article.title and article.url
    ]
    if not articles_list:
        raise ValueError("No valid articles available to format.")

    timestamp = datetime.now(timezone.utc)
    filename_stem = timestamp.strftime("news-%Y%m%d-%H%M%S")

    if format.lower() != "markdown":
        raise ValueError("Stage 1 supports only markdown output.")

    lines = [
        f"# Daily News Digest ({timestamp.date().isoformat()})",
        "",
        f"Generated on {timestamp.strftime('%Y-%m-%d %H:%M UTC')}.",
        "",
    ]

    for index, article in enumerate(articles_list, start=1):
        lines.append(f"## {index}. {article.title}")
        if article.source:
            lines.append(f"*Source:* {article.source}")
        published_value = _format_timestamp(article.published_at)
        lines.append(f"*Published:* {published_value}")
        if article.description:
            lines.append("")
            lines.append(article.description.strip())
        lines.append("")
        lines.append(f"[Read more]({article.url})")
        lines.append("")

    content = "\n".join(lines).strip() + "\n"
    filename = f"{filename_stem}.md"
    logger.debug("Generated document %s (%s bytes)", filename, len(content))
    return filename, content.encode("utf-8")


def save_document(path: str | Path, content: bytes) -> None:
    """Persist document content to disk."""

    destination = Path(path)
    destination.write_bytes(content)
    logger.info("Saved document to %s", destination)
