import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

try:  # pragma: no cover - the real dependency exists in production
    import aiohttp  # type: ignore  # noqa: F401
except ImportError:  # pragma: no cover - provide a minimal stub for tests
    sys.modules.setdefault("aiohttp", SimpleNamespace(ClientSession=object))

from src.cursor import cli as cursor_cli


@pytest.mark.asyncio()
async def test_cursor_start_invokes_selected_subsystems(monkeypatch):
    calls = SimpleNamespace(auto=0, knowledge=0, mobile=0, brain=0)

    async def fake_auto(paths):
        calls.auto += 1
        assert paths == [Path(".")]

    async def fake_knowledge():
        calls.knowledge += 1

    async def fake_mobile():
        calls.mobile += 1

    async def fake_brain():
        calls.brain += 1

    monkeypatch.setattr(cursor_cli, "start_cursor_auto_invocation", fake_auto)
    monkeypatch.setattr(cursor_cli, "start_knowledge_auto_loading", fake_knowledge)
    monkeypatch.setattr(cursor_cli, "start_mobile_app", fake_mobile)
    monkeypatch.setattr(cursor_cli, "start_brain_blocks_integration", fake_brain)

    exit_code = await cursor_cli._run_start(
        watch=[Path(".")],
        include_knowledge=True,
        include_mobile=True,
        include_brain_blocks=True,
        stay_alive=False,
    )

    assert exit_code == 0
    assert calls.auto == 1
    assert calls.knowledge == 1
    assert calls.mobile == 1
    assert calls.brain == 1


def test_cursor_validate_and_status(monkeypatch, capsys):
    monkeypatch.setattr(cursor_cli, "validate_cursor_compliance", lambda: True)
    monkeypatch.setattr(
        cursor_cli,
        "get_cursor_usage_report",
        lambda: {"compliance_status": "COMPLIANT", "summary": "ok"},
    )

    assert cursor_cli._run_validate() == 0
    assert cursor_cli._run_status() == 0

    captured = capsys.readouterr().out
    assert "COMPLIANT" in captured


@pytest.mark.asyncio()
async def test_cursor_rules_command(monkeypatch, capsys):
    class DummyInvoker:
        def get_rule_stats(self):
            return {"rules": 2}

    monkeypatch.setattr(cursor_cli, "get_auto_invoker", lambda: DummyInvoker())

    assert await cursor_cli._run_rules() == 0
    captured = capsys.readouterr().out
    assert "rules" in captured

    await asyncio.sleep(0)
