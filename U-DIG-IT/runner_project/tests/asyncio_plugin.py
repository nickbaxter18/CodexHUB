"""Lightweight pytest plugin to execute asyncio tests without external dependencies."""

from __future__ import annotations

import asyncio
import inspect
from typing import Any

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register the asyncio marker for documentation purposes."""

    config.addinivalue_line(
        "markers", "asyncio: mark test to run using an event loop provided by the plugin"
    )


def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> Any:
    """Execute coroutine test functions inside a fresh event loop.

    This mirrors the minimal behaviour required from pytest-asyncio for the Stage 1
    test-suite, avoiding an additional runtime dependency.
    """

    marker = pyfuncitem.get_closest_marker("asyncio")
    if marker is None:
        return None

    testfunction = pyfuncitem.obj
    if not inspect.iscoroutinefunction(testfunction):
        return None

    call_args = {
        name: pyfuncitem.funcargs[name]
        for name in pyfuncitem._fixtureinfo.argnames
        if name in pyfuncitem.funcargs
    }

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(testfunction(**call_args))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        asyncio.set_event_loop(None)
        loop.close()

    return True
