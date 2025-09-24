"""Concurrency helpers for the runner."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Awaitable, Callable, Dict

_executors: Dict[str, ThreadPoolExecutor] = {}


def get_executor(kind: str = "io") -> ThreadPoolExecutor:
    """Return a lazily created executor segregated by workload type."""

    kind = kind.lower()
    if kind not in {"io", "cpu"}:
        raise ValueError("Executor kind must be 'io' or 'cpu'")
    if kind not in _executors:
        max_workers = 8 if kind == "io" else 4
        _executors[kind] = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix=f"runner-{kind}"
        )
    return _executors[kind]


async def run_in_thread(
    func: Callable[..., Any], *args: Any, kind: str = "io", **kwargs: Any
) -> Any:
    """Run a blocking function in the selected executor."""

    loop = asyncio.get_running_loop()
    executor = get_executor(kind)
    return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))


async def gather_with_concurrency(*aws: Awaitable[Any]) -> Any:
    """Gather awaitables ensuring they run concurrently."""

    return await asyncio.gather(*aws)
