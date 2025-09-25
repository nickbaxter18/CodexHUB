import re
from datetime import datetime, timezone

import pytest

from src.document_formatter import create_document
from src.news_fetcher import NewsArticle


def make_article(title: str = "Title") -> NewsArticle:
    return NewsArticle(
        title=title,
        description="Summary",
        url="https://example.com",
        published_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        source="Example",
    )


def test_create_document_generates_markdown() -> None:
    filename, content = create_document([make_article("Headline")])

    assert filename.endswith(".md")
    text = content.decode("utf-8")
    assert "# Daily News Digest" in text
    assert "## 1. Headline" in text
    assert "[Read more](https://example.com)" in text


def test_create_document_requires_articles() -> None:
    with pytest.raises(ValueError):
        create_document([])


def test_create_document_supports_multiple_articles() -> None:
    _, content = create_document([make_article("A"), make_article("B")])
    text = content.decode("utf-8")
    assert len(re.findall(r"## \d+.", text)) >= 2


def test_create_document_rejects_other_formats() -> None:
    with pytest.raises(ValueError):
        create_document([make_article()], format="google-docs")
