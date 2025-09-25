"""Entry point for the Google News Drive Sync pipeline."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any, Dict

from .document_formatter import create_document
from .drive_client import DriveClient, DriveClientError
from .news_fetcher import fetch_news
from .scheduler import schedule
from .utils import load_config, setup_logging

logger = logging.getLogger(__name__)


def _run_once(config: Dict[str, Any]) -> None:
    news_cfg = config.get("news_api", {})
    document_cfg = config.get("document", {})
    drive_cfg = config.get("drive", {})

    api_key = news_cfg.get("api_key")
    if not api_key:
        raise ValueError("news_api.api_key is required")

    topics = news_cfg.get("topics") or []
    query = {
        "language": news_cfg.get("language", "en"),
        "country": news_cfg.get("country"),
        "pageSize": news_cfg.get("page_size", 20),
    }
    if topics:
        query["q"] = " OR ".join(topics)
    if news_cfg.get("max_articles"):
        query["max_articles"] = news_cfg["max_articles"]

    base_url = news_cfg.get("base_url", "https://newsapi.org/v2/top-headlines")
    articles = fetch_news(
        api_key,
        query,
        base_url=base_url,
        max_articles=news_cfg.get("max_articles"),
    )
    if not articles:
        logger.warning("No articles retrieved; skipping upload.")
        return

    filename, content = create_document(
        articles,
        format=document_cfg.get("format", "markdown"),
        timezone_name=document_cfg.get("timezone"),
    )

    credentials_key = "oauth_credentials_path"
    credentials_path = drive_cfg.get(credentials_key, "credentials.json")
    client = DriveClient(credentials_path)
    client.authenticate()
    folder_name = drive_cfg.get("folder_name", "News")
    folder_id = client.get_or_create_folder(folder_name)
    client.upload_document(folder_id, filename, content)
    logger.info("Uploaded document %s", filename)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Google News Drive Sync")
    parser.add_argument(
        "--config",
        default=Path("config/config.yaml"),
        help="Path to the YAML configuration file",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run the pipeline once and skip scheduling.",
    )
    args = parser.parse_args(argv)

    setup_logging()
    config = load_config(args.config)

    try:
        _run_once(config)
    except DriveClientError:
        logger.exception("Drive upload failed")
        raise

    if args.once:
        return

    scheduler_cfg = config.get("scheduler", {})
    interval = scheduler_cfg.get("update_interval_minutes")
    if not interval:
        return

    schedule(lambda: _run_once(config), int(interval))

    # Keep the main thread alive when scheduling is enabled.
    try:  # pragma: no cover - interactive run loop
        import time

        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal; exiting.")


if __name__ == "__main__":  # pragma: no cover
    main()
