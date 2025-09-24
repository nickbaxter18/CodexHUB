"""Security utilities."""

from __future__ import annotations

import hashlib
import secrets


def hash_secret(secret: str) -> str:
    salt = secrets.token_hex(8)
    digest = hashlib.sha256((salt + secret).encode("utf-8")).hexdigest()
    return f"{salt}:{digest}"


def verify_secret(secret: str, hashed: str) -> bool:
    salt, digest = hashed.split(":", 1)
    return hashlib.sha256((salt + secret).encode("utf-8")).hexdigest() == digest
