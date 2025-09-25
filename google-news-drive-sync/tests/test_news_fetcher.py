import pytest
import requests

from src.news_fetcher import NewsFetcherError, fetch_news


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self._responses = responses
        self.calls = 0

    def get(self, *args, **kwargs):  # noqa: D401 - behave like requests.Session.get
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

    articles = fetch_news("key", {"pageSize": 5}, session=session)

    assert len(articles) == 1
    article = articles[0]
    assert article.title == "Example"
    assert article.source == "Example Source"
    assert article.url == "https://example.com"


def test_fetch_news_handles_rate_limit():
    responses = [FakeResponse(429, {})]
    session = FakeSession(responses)

    with pytest.raises(NewsFetcherError):
        fetch_news("key", {}, session=session)


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

    articles = fetch_news("key", {}, session=session)
    assert len(articles) == 1
    assert articles[0].title == "Valid"
