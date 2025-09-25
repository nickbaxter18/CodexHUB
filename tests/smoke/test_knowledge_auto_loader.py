import asyncio
from types import SimpleNamespace

import pytest

from src.knowledge import auto_loader


@pytest.mark.asyncio()
async def test_start_knowledge_auto_loading_respects_toggle(monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_AUTO_LOAD", "false")

    called = False

    async def fail_start():  # pragma: no cover - should not run
        nonlocal called
        called = True

    monkeypatch.setattr(
        auto_loader,
        "get_auto_loader",
        lambda: SimpleNamespace(start_auto_loading=fail_start),
    )

    await auto_loader.start_knowledge_auto_loading()
    assert called is False


@pytest.mark.asyncio()
async def test_start_knowledge_auto_loading_executes_when_enabled(monkeypatch):
    monkeypatch.delenv("KNOWLEDGE_AUTO_LOAD", raising=False)

    called = False

    async def start():
        nonlocal called
        called = True

    monkeypatch.setattr(
        auto_loader,
        "get_auto_loader",
        lambda: SimpleNamespace(start_auto_loading=start),
    )

    await auto_loader.start_knowledge_auto_loading()
    assert called is True

    await asyncio.sleep(0)
