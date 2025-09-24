"""Simple caching utilities for Stage 2 features."""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Generic, Optional, Tuple, TypeVar

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class CacheEntry(Generic[V]):
    """Container storing cached values with an expiry timestamp."""

    value: V
    expires_at: float


class SimpleCache(Generic[K, V]):
    """A tiny LRU cache with optional time-based invalidation."""

    def __init__(self, maxsize: int = 128, ttl: Optional[float] = 300.0) -> None:
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        self._maxsize = maxsize
        self._ttl = ttl
        self._store: OrderedDict[K, CacheEntry[V]] = OrderedDict()

    def _purge_expired(self) -> None:
        now = time.monotonic()
        expired_keys = [
            key
            for key, entry in self._store.items()
            if entry.expires_at != float("inf") and entry.expires_at < now
        ]
        for key in expired_keys:
            self._store.pop(key, None)

    def get(self, key: K) -> Optional[V]:
        """Retrieve a cached value if still valid."""

        self._purge_expired()
        entry = self._store.get(key)
        if entry is None:
            return None
        # Refresh key order for LRU behaviour.
        self._store.move_to_end(key)
        return entry.value

    def set(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        """Store a value in the cache."""

        self._purge_expired()
        expiry = float("inf")
        timeout = ttl if ttl is not None else self._ttl
        if timeout is not None:
            expiry = time.monotonic() + timeout
        self._store[key] = CacheEntry(value=value, expires_at=expiry)
        self._store.move_to_end(key)
        if len(self._store) > self._maxsize:
            self._store.popitem(last=False)

    def clear(self) -> None:
        """Remove all cached entries."""

        self._store.clear()

    def snapshot(self) -> Tuple[Tuple[K, V], ...]:
        """Return a snapshot of the current cache contents for debugging/tests."""

        self._purge_expired()
        return tuple((key, entry.value) for key, entry in self._store.items())
