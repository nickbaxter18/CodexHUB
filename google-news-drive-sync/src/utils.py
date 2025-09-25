"""Utility helpers for Google News Drive Sync."""

from __future__ import annotations

import base64
import functools
import hashlib
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, TypeVar

import yaml

T = TypeVar("T")


try:  # pragma: no cover - dependency optional for tests
    from cryptography.fernet import Fernet
except Exception:  # pragma: no cover - optional dependency not installed
    Fernet = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


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


def load_env_file(path: str | Path) -> None:
    """Load environment variables from a ``.env`` file when supported."""

    env_path = Path(path)
    if not env_path.exists():
        return

    try:
        from dotenv import dotenv_values
    except ImportError:  # pragma: no cover - optional dependency
        logger.debug(
            "python-dotenv not installed; skipping env file %s",
            env_path,
        )
        return

    values = dotenv_values(env_path)
    for key, value in values.items():
        if value is not None and key not in os.environ:
            os.environ[key] = value


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


class TokenEncryptor:
    """Symmetric encryption helper for Drive tokens."""

    def __init__(self, key: bytes) -> None:
        if not key:
            raise ValueError("Encryption key must not be empty")
        self._key = hashlib.sha256(key).digest()
        self._fernet: Optional[Fernet] = None
        if Fernet is not None:  # pragma: no cover
            fernet_key = base64.urlsafe_b64encode(self._key)
            self._fernet = Fernet(fernet_key)

    @classmethod
    def from_password(cls, password: str) -> "TokenEncryptor":
        return cls(password.encode("utf-8"))

    def encrypt(self, payload: bytes) -> bytes:
        if self._fernet is not None:
            return self._fernet.encrypt(payload)
        return _xor_bytes(payload, self._key)

    def decrypt(self, payload: bytes) -> bytes:
        if self._fernet is not None:
            return self._fernet.decrypt(payload)
        return _xor_bytes(payload, self._key)


def utcnow() -> datetime:
    """Return a timezone-aware ``datetime`` in UTC."""

    return datetime.now(timezone.utc)
