"""Utility helpers for Google News Drive Sync."""

from __future__ import annotations

import functools
import logging
import time
from pathlib import Path
from typing import Any, Callable, Iterable, TypeVar

import yaml

T = TypeVar("T")


def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with a standard format.

    The configuration is idempotent; repeated calls do not add
    duplicate handlers.
    """

    logger = logging.getLogger()
    if logger.handlers:
        logger.setLevel(level)
        return

    handler = logging.StreamHandler()
    format_pattern = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(format_pattern)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)


def retry(
    exceptions: Iterable[type[BaseException]],
    tries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry decorator with exponential backoff."""

    exception_types = tuple(exceptions)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            attempts = 0
            wait = delay
            while True:
                try:
                    return func(*args, **kwargs)
                except exception_types:  # type: ignore[arg-type]
                    attempts += 1
                    if attempts >= tries:
                        raise
                    time.sleep(wait)
                    wait *= backoff

        return wrapper

    return decorator


def load_config(path: str | Path) -> dict[str, Any]:
    """Load YAML configuration from *path*."""

    config_path = Path(path)
    if not config_path.exists():
        message = f"Configuration file not found: {config_path}"
        raise FileNotFoundError(message)

    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        error_msg = "Configuration file must define a top-level mapping."
        raise ValueError(error_msg)

    return data
