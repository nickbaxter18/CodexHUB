import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from src.execution import cursor_adapter
from src.types import CursorInvocationRequest


@pytest.mark.asyncio
async def test_cursor_adapter_invokes_cli(monkeypatch: Any) -> None:
    cursor_adapter.clear_cache()
    request = CursorInvocationRequest(prompt="generate", apply_changes=False)

    with (
        patch("shutil.which", return_value="/usr/bin/cursor"),
        patch(
            "subprocess.run",
            return_value=SimpleNamespace(
                stdout=json.dumps({"message": "ok"}), stderr="", returncode=0
            ),
        ) as mocked_run,
    ):
        result = await cursor_adapter.run_cursor(request)

    assert result.suggestions["message"] == "ok"
    mocked_run.assert_called_once()

    # Second invocation should hit the cache and avoid another subprocess call.
    with (
        patch("shutil.which", return_value="/usr/bin/cursor"),
        patch("subprocess.run") as second_run,
    ):
        cached = await cursor_adapter.run_cursor(request)
    assert cached.stdout == result.stdout
    second_run.assert_not_called()

    cursor_adapter.clear_cache()
