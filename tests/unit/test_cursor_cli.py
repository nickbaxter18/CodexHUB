import asyncio
import sys
import types
from pathlib import Path

import pytest


class _DummySession:
    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self) -> "_DummySession":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def post(
        self, *args: object, **kwargs: object
    ) -> None:  # pragma: no cover - not used in tests
        raise RuntimeError("aiohttp stub does not support network calls")


class _DummyTimeout:
    def __init__(self, *args, **kwargs) -> None:
        pass


aiohttp_stub = types.ModuleType("aiohttp")
aiohttp_stub.ClientSession = _DummySession
aiohttp_stub.ClientTimeout = _DummyTimeout
sys.modules.setdefault("aiohttp", aiohttp_stub)

from src.cursor import cli  # noqa: E402


def test_validate_exit_codes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "validate_cursor_compliance", lambda: True)
    assert cli.main(["validate"]) == 0

    monkeypatch.setattr(cli, "validate_cursor_compliance", lambda: False)
    assert cli.main(["validate"]) == 1


def test_status_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli,
        "get_cursor_usage_report",
        lambda: {"compliance_status": "COMPLIANT", "usage_statistics": {}},
    )
    assert cli.main(["status"]) == 0

    monkeypatch.setattr(
        cli,
        "get_cursor_usage_report",
        lambda: {"compliance_status": "NON_COMPLIANT", "usage_statistics": {}},
    )
    assert cli.main(["status"]) == 1


def test_start_invocation(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, int] = {"auto": 0, "knowledge": 0}

    async def fake_auto_invocation(paths: list[Path]) -> None:
        calls["auto"] += 1
        assert paths

    async def fake_knowledge() -> None:
        calls["knowledge"] += 1

    monkeypatch.setattr(cli, "start_cursor_auto_invocation", fake_auto_invocation)
    monkeypatch.setattr(cli, "start_knowledge_auto_loading", fake_knowledge)

    async def runner() -> int:
        return await cli._run_start(  # type: ignore[attr-defined]
            watch=[Path(".")],
            include_knowledge=True,
            include_mobile=False,
            include_brain_blocks=False,
            stay_alive=False,
        )

    assert asyncio.run(runner()) == 0
    assert calls == {"auto": 1, "knowledge": 1}
