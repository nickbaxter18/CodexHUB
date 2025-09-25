import asyncio

import pytest

from src.news_fetcher import fetch_news, fetch_news_async


class FakeResponse:
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return self._payload

    async def text(self):  # pragma: no cover - only used when raising errors
        return "error"


class FakeSession:
    def __init__(self, responses):
        self._responses = responses
        self.calls = 0

    def get(self, *args, **kwargs):  # noqa: D401 - mimic aiohttp session
        response = self._responses[self.calls]
        self.calls += 1
        return response


def test_fetch_news_collects_articles():
    article_payload = {
        "title": "Example",
        "description": "desc",
        "url": "https://example.com",
        "publishedAt": "2023-01-01T00:00:00Z",
        "source": {"name": "Example Source"},
    }
    responses = [
        FakeResponse(
            200,
            {
                "articles": [article_payload],
                "totalResults": 1,
            },
        )
    ]
    session = FakeSession(responses)

    articles = asyncio.run(fetch_news_async("key", {"pageSize": 5}, session=session))

    assert len(articles) == 1
    article = articles[0]
    assert article.title == "Example"
    assert article.source == "Example Source"
    assert article.url == "https://example.com"


def test_fetch_news_handles_rate_limit(caplog):
    responses = [FakeResponse(429, {})]
    session = FakeSession(responses)

    with caplog.at_level("ERROR"):
        articles = asyncio.run(fetch_news_async("key", {}, session=session))

    assert articles == []
    assert any("Rate limit" in message for message in caplog.text.splitlines())


def test_fetch_news_requires_api_key():
    with pytest.raises(ValueError):
        fetch_news("", {})


def test_fetch_news_skips_invalid_payload():
    responses = [
        FakeResponse(
            200,
            {
                "articles": [
                    {"title": None, "url": ""},
                    "not-a-dict",
                    {
                        "title": "Valid",
                        "description": "desc",
                        "url": "https://valid.example.com",
                    },
                ]
            },
        ),
        FakeResponse(200, {"articles": []}),
    ]
    session = FakeSession(responses)

    articles = asyncio.run(fetch_news_async("key", {}, session=session))
    assert len(articles) == 1
    assert articles[0].title == "Valid"
