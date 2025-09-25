import asyncio

from src.rss_fetcher import fetch_rss_async


class FakeResponse:
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def text(self):
        return self._payload


class FakeSession:
    def __init__(self, response):
        self._response = response
        self.calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        return self._response


def test_fetch_rss_parses_feed():
    feed = """
    <rss><channel><title>Feed</title>
        <item>
            <title>Headline</title>
            <link>https://example.com</link>
            <description>Summary</description>
            <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
        </item>
    </channel></rss>
    """
    session = FakeSession(FakeResponse(200, feed))

    articles = asyncio.run(fetch_rss_async(["https://feed"], session=session))

    assert len(articles) == 1
    article = articles[0]
    assert article.title == "Headline"
    assert article.url == "https://example.com"
    assert article.source == "Feed"


def test_fetch_rss_handles_http_errors(caplog):
    session = FakeSession(FakeResponse(500, "error"))
    with caplog.at_level("ERROR"):
        articles = asyncio.run(fetch_rss_async(["https://feed"], session=session))

    assert articles == []
    assert "RSS request failed" in caplog.text
