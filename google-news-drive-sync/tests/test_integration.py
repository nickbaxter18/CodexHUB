from unittest import mock

import importlib

from src.news_fetcher import NewsArticle

main_module = importlib.import_module("src.main")


def test_run_once_flow(monkeypatch):
    articles = [
        NewsArticle(
            title="Headline",
            description="Summary",
            url="https://example.com",
            published_at=None,
            source="Example",
        )
    ]

    monkeypatch.setattr(main_module, "fetch_all_articles", mock.AsyncMock(return_value=articles))
    monkeypatch.setattr(
        main_module,
        "create_document",
        mock.Mock(return_value=("file.md", b"content")),
    )

    fake_client = mock.Mock()
    fake_client.get_or_create_folder.return_value = "folder"

    class FakeDriveClient:
        def __init__(self, *args, **kwargs):
            self.instance = fake_client

        def authenticate(self):
            return None

        def get_or_create_folder(self, name):
            return fake_client.get_or_create_folder(name)

        def upload_document(self, folder_id, filename, content):
            return fake_client.upload_document(folder_id, filename, content)

    monkeypatch.setattr(main_module, "DriveClient", FakeDriveClient)

    config = {
        "news_api": {"api_key": "key", "topics": ["tech"], "base_url": "url"},
        "document": {"format": "markdown"},
        "drive": {"folder_name": "News", "oauth_credentials_path": "creds.json"},
        "cache": {"enabled": False},
        "scheduler": {"enabled": False},
        "secrets": {},
        "repository": {"enabled": False},
    }

    monkeypatch.setattr(main_module, "load_config", mock.Mock(return_value=config))
    monkeypatch.setattr(main_module, "setup_logging", mock.Mock())
    monkeypatch.setattr(main_module, "load_env_file", mock.Mock())

    with mock.patch("pathlib.Path.exists", return_value=True):
        main_module.main(["--config", "config/config.yaml", "--once"])

    fake_client.upload_document.assert_called_once()
