import shutil
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from src.errors import GitError
from src.execution.git_actions import run_git_action
from src.types import GitActionRequest


@pytest.mark.asyncio
async def test_git_status(tmp_path_factory: Any) -> None:
    repo_dir = Path.cwd() / "tests" / "git_repo"
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    repo_dir.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    request = GitActionRequest(action="status", cwd=repo_dir)
    result = await run_git_action(request)
    assert "On branch" in result.stdout


@pytest.mark.asyncio
async def test_git_invalid_action(tmp_path_factory: Any) -> None:
    repo_dir = Path.cwd() / "tests" / "git_repo_invalid"
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    repo_dir.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)

    request = GitActionRequest(action="nonexistent", cwd=repo_dir)
    with pytest.raises(GitError):
        await run_git_action(request)


@pytest.mark.asyncio
async def test_git_conflict_returns_result(tmp_path: Any) -> None:
    repo_dir = Path.cwd() / "tests" / "git_repo_conflict"
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    repo_dir.mkdir(parents=True)

    request = GitActionRequest(action="merge", args=["feature"], cwd=repo_dir)

    conflict = subprocess.CompletedProcess(
        args=["git", "merge"],
        returncode=1,
        stdout="",
        stderr="CONFLICT (content): Merge conflict in file",
    )

    with patch("src.execution.git_actions._execute", return_value=conflict):
        result = await run_git_action(request)
    assert result.return_code == 1
    assert "CONFLICT" in result.stderr
