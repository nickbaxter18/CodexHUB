"""Secure command execution utilities."""

from __future__ import annotations

import subprocess
from subprocess import TimeoutExpired
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from ..config import get_config
from ..errors import CommandError
from ..types import CommandRequest, CommandResult
from ..utils.concurrency import run_in_thread
from ..utils.logger import get_logger
from ..utils.validators import ensure_safe_path, sanitize_args, validate_command

LOGGER = get_logger("command_runner")


def _execute(command: List[str], cwd: Path, timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


async def run_command(request: CommandRequest) -> CommandResult:
    """Execute a command securely."""

    validate_command(request.command)
    args = sanitize_args(request.args)
    config = get_config()
    cwd = ensure_safe_path(request.cwd or config.root_dir)
    timeout = request.timeout or config.default_timeout
    command = [request.command, *args]
    started_at = datetime.now(timezone.utc)

    LOGGER.info("Executing command: %s", command)

    def runner() -> subprocess.CompletedProcess[str]:
        return _execute(command, cwd, timeout)

    try:
        completed = await run_in_thread(runner)
    except TimeoutExpired as exc:
        LOGGER.error("Command timed out: %s", command)
        raise CommandError("Command timed out") from exc
    completed_at = datetime.now(timezone.utc)

    if completed.returncode != 0:
        LOGGER.error("Command failed: %s", completed.stderr.strip())
        raise CommandError(
            message=completed.stderr.strip() or "Command execution failed",
            return_code=completed.returncode,
        )

    return CommandResult(
        stdout=completed.stdout,
        stderr=completed.stderr,
        return_code=completed.returncode,
        started_at=started_at,
        completed_at=completed_at,
    )
