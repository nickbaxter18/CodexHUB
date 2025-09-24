"""Git action helpers."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from subprocess import TimeoutExpired
from typing import List

from ..config import get_config
from ..errors import GitError
from ..types import GitActionRequest, GitActionResult
from ..utils.concurrency import run_in_thread
from ..utils.logger import get_logger
from ..utils.validators import ensure_safe_path, sanitize_args, validate_command

LOGGER = get_logger("git_actions")


def _execute(command: List[str], cwd: Path, timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


async def run_git_action(request: GitActionRequest) -> GitActionResult:
    """Execute a git action with validation."""

    validate_command("git")
    supported_actions = {"status", "fetch", "pull", "push", "checkout", "merge", "rebase"}
    if request.action not in supported_actions:
        raise GitError(f"Unsupported git action: {request.action}", action=request.action)
    args = sanitize_args(request.args)
    config = get_config()
    cwd = ensure_safe_path(request.cwd or config.root_dir)
    timeout = request.timeout or config.git_timeout
    command = ["git", request.action, *args]
    started_at = datetime.now(timezone.utc)

    LOGGER.info("Running git action: %s", command)

    def runner() -> subprocess.CompletedProcess[str]:
        return _execute(command, cwd, timeout)

    try:
        completed = await run_in_thread(runner)
    except TimeoutExpired as exc:
        LOGGER.error("Git action timed out: %s", command)
        raise GitError("Git action timed out", action=request.action) from exc
    completed_at = datetime.now(timezone.utc)

    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        if "CONFLICT" in stderr.upper():
            LOGGER.warning("Git action reported conflicts: %s", stderr)
        else:
            LOGGER.error("Git action failed: %s", stderr)
            raise GitError(
                message=stderr or "Git action failed",
                action=request.action,
            )

    return GitActionResult(
        stdout=completed.stdout,
        stderr=completed.stderr,
        return_code=completed.returncode,
        action=request.action,
        started_at=started_at,
        completed_at=completed_at,
    )
