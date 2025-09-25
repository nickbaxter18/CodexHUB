"""Entry point for the Google News Drive Sync pipeline."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import threading
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Dict, Optional

from .api_router import fetch_all_articles
from .cache import ArticleCache
from .document_formatter import create_document
from .drive_client import DriveClient, DriveClientError, TokenStorage
from .news_fetcher import NewsArticle
from .article_repository import ArticleRepository
from .monitor import MonitoringClient
from .scheduler import SchedulerHandle, schedule
from .utils import (
    TokenEncryptor,
    load_config,
    load_env_file,
    setup_logging,
)
from .server import RateLimiter, create_app, run_server

logger = logging.getLogger(__name__)


def _build_cache(
    config: Dict[str, Any],
    base_dir: Path,
) -> ArticleCache | None:
    cache_cfg = config.get("cache", {})
    if cache_cfg and not cache_cfg.get("enabled", True):
        return None
    default_path = base_dir.parent / "cache" / "articles.db"
    cache_path = cache_cfg.get("path", default_path)
    cache_path = Path(cache_path)
    if not cache_path.is_absolute():
        cache_path = base_dir / cache_path
    retention = int(cache_cfg.get("retention_days", 7))
    return ArticleCache(cache_path, retention_days=retention)


def _resolve_encryptor(config: Dict[str, Any]) -> Optional[TokenEncryptor]:
    secrets_cfg = config.get("secrets", {})
    password = secrets_cfg.get("encryption_key")
    env_var = secrets_cfg.get("encryption_key_env", "TOKEN_ENCRYPTION_KEY")
    password = password or os.environ.get(env_var)
    if not password:
        return None
    try:
        return TokenEncryptor.from_password(password)
    except ValueError:
        logger.warning("Invalid encryption key; Drive tokens will not be encrypted")
        return None


async def _collect_articles(
    config: Dict[str, Any],
    cache: ArticleCache | None,
    monitor: MonitoringClient | None,
    base_dir: Path,
) -> list[NewsArticle]:
    articles = await fetch_all_articles(
        config,
        cache=cache,
        monitor=monitor,
        base_dir=base_dir,
    )
    if monitor is not None:
        monitor.record_articles("aggregated", len(articles))
    return articles


def _create_drive_client(
    drive_cfg: Dict[str, Any],
    encryptor: TokenEncryptor | None,
    base_dir: Path,
) -> DriveClient:
    credentials_path = drive_cfg.get(
        "oauth_credentials_path",
        "credentials.json",
    )
    credentials_path = Path(credentials_path)
    if not credentials_path.is_absolute():
        credentials_path = base_dir / credentials_path

    token_storage: TokenStorage | None = None
    token_path = drive_cfg.get("token_storage_path")
    if token_path:
        token_path = Path(token_path)
        if not token_path.is_absolute():
            token_path = base_dir / token_path
        token_storage = TokenStorage(token_path, encryptor=encryptor)

    return DriveClient(
        str(credentials_path),
        token_storage=token_storage,
    )


def _run_once(
    config: Dict[str, Any],
    *,
    cache: ArticleCache | None,
    monitor: MonitoringClient | None,
    encryptor: TokenEncryptor | None,
    base_dir: Path,
    repository: ArticleRepository | None,
) -> None:
    document_cfg = config.get("document", {})
    drive_cfg = config.get("drive", {})

    if monitor is not None:
        monitor.start_run()

    try:
        latency_cm = monitor.track_latency("fetch") if monitor is not None else nullcontext()
        with latency_cm:
            articles = asyncio.run(_collect_articles(config, cache, monitor, base_dir))
    except Exception:
        if monitor is not None:
            monitor.complete_run(status="error")
        raise

    if not articles:
        logger.warning("No new articles retrieved; skipping upload.")
        if monitor is not None:
            monitor.complete_run(status="skipped")
        return

    if repository is not None:
        repository.persist(articles)
        if monitor is not None:
            monitor.record_queue_depth(repository.count())

    format_cm = monitor.track_latency("format") if monitor is not None else nullcontext()
    with format_cm:
        filename, content = create_document(
            articles,
            format=document_cfg.get("format", "markdown"),
            timezone_name=document_cfg.get("timezone"),
        )

    upload_cm = monitor.track_latency("upload") if monitor is not None else nullcontext()
    with upload_cm:
        client = _create_drive_client(drive_cfg, encryptor, base_dir)
        client.authenticate()
        folder_name = drive_cfg.get("folder_name", "News")
        folder_id = client.get_or_create_folder(folder_name)
        client.upload_document(folder_id, filename, content)
    logger.info("Uploaded document %s", filename)
    if monitor is not None:
        monitor.record_document_upload()
        monitor.complete_run(status="success")
        monitor.emit()


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
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Expose the FastAPI dashboard while the scheduler runs.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Hostname for the dashboard server.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the dashboard server.",
    )
    args = parser.parse_args(argv)

    setup_logging()
    config_path = Path(args.config)
    config = load_config(config_path)

    secrets_cfg = config.get("secrets", {})
    env_file = secrets_cfg.get("env_file")
    if env_file:
        env_path = Path(env_file)
        if not env_path.is_absolute():
            env_path = config_path.parent / env_file
        load_env_file(env_path)

    base_dir = config_path.parent
    cache = _build_cache(config, base_dir)
    repository_cfg = config.get("repository", {})
    repository: ArticleRepository | None = None
    if repository_cfg.get("enabled", True):
        repo_path = repository_cfg.get("path")
        if repo_path:
            repo_path = Path(repo_path)
            if not repo_path.is_absolute():
                repo_path = base_dir / repo_path
        else:
            repo_path = base_dir / "../cache/articles.db"
        repository = ArticleRepository(repo_path)
    monitor = MonitoringClient()
    encryptor = _resolve_encryptor(config)
    server_cfg = config.get("server", {})
    server_host = server_cfg.get("host", args.host)
    server_port = int(server_cfg.get("port", args.port))
    auth_cfg = server_cfg.get("auth", {}) if isinstance(server_cfg, dict) else {}
    api_keys = [key for key in auth_cfg.get("api_keys", []) if key]
    rate_cfg = server_cfg.get("rate_limit", {}) if isinstance(server_cfg, dict) else {}
    rate_limiter: RateLimiter | None = None
    if rate_cfg:
        try:
            requests_per_minute = int(rate_cfg.get("requests_per_minute", 0))
        except (TypeError, ValueError):
            requests_per_minute = 0
        window_seconds = float(rate_cfg.get("window_seconds", 60))
        if requests_per_minute > 0:
            rate_limiter = RateLimiter(requests_per_minute, window_seconds=window_seconds)

    try:
        _run_once(
            config,
            cache=cache,
            monitor=monitor,
            encryptor=encryptor,
            base_dir=base_dir,
            repository=repository,
        )
    except DriveClientError:
        logger.exception("Drive upload failed")
        raise

    if args.once:
        return

    scheduler_cfg = config.get("scheduler", {})
    enabled = scheduler_cfg.get("enabled", True)
    if not enabled:
        return

    interval = scheduler_cfg.get("update_interval_minutes")
    cron_cfg = scheduler_cfg.get("cron")
    timezone = scheduler_cfg.get("timezone")

    if not interval and not cron_cfg:
        logger.warning("Scheduler enabled but no interval or cron specified; skipping")
        return

    def job() -> None:
        _run_once(
            config,
            cache=cache,
            monitor=monitor,
            encryptor=encryptor,
            base_dir=base_dir,
            repository=repository,
        )

    handle: SchedulerHandle = schedule(
        job,
        interval_minutes=int(interval) if interval else None,
        cron=cron_cfg,
        timezone=timezone,
    )

    server_thread: threading.Thread | None = None
    if args.serve:
        app = create_app(
            repository=repository,
            monitor=monitor,
            api_keys=api_keys,
            rate_limiter=rate_limiter,
        )

        def _serve() -> None:  # pragma: no cover - interactive behaviour
            run_server(app, host=server_host, port=server_port)

        server_thread = threading.Thread(
            target=_serve,
            daemon=True,
        )
        server_thread.start()

    try:  # pragma: no cover - interactive run loop
        import time

        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal; exiting.")
        handle.shutdown()


if __name__ == "__main__":  # pragma: no cover
    main()
