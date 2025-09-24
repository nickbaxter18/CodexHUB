from pathlib import Path

import pytest
from pytest import TempPathFactory

from src.errors import CommandError, ValidationError
from src.execution.command_runner import run_command
from src.types import CommandRequest


@pytest.mark.asyncio
async def test_run_allowed_command() -> None:
    request = CommandRequest(command="echo", args=["hello"])
    result = await run_command(request)
    assert "hello" in result.stdout
    assert result.return_code == 0


@pytest.mark.asyncio
async def test_disallowed_command() -> None:
    request = CommandRequest(command="rm")
    with pytest.raises(ValidationError):
        await run_command(request)


@pytest.mark.asyncio
async def test_rejects_cwd_outside_project() -> None:
    root = Path.cwd()
    malicious = root.parent / f"{root.name}-escape"
    malicious.mkdir(exist_ok=True)

    try:
        request = CommandRequest(
            command="echo",
            args=["blocked"],
            cwd=malicious,
        )

        with pytest.raises(ValidationError):
            await run_command(request)
    finally:
        if malicious.exists():
            malicious.rmdir()


@pytest.mark.asyncio
async def test_command_timeout(tmp_path_factory: TempPathFactory) -> None:
    script_dir = Path.cwd() / "tests" / "artifacts"
    script_dir.mkdir(parents=True, exist_ok=True)
    script_path = script_dir / "sleep_script.py"
    script_path.write_text("import time\n" "time.sleep(1)\n")

    request = CommandRequest(
        command="python",
        args=[str(script_path)],
        timeout=0.1,
    )

    try:
        with pytest.raises(CommandError):
            await run_command(request)
    finally:
        if script_path.exists():
            script_path.unlink()
