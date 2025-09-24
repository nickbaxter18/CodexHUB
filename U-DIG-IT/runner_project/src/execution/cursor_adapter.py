"""Cursor CLI integration used for Stage 2 code operations."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Dict

from ..config import get_config
from ..errors import CursorError
from ..types import CursorInvocationRequest, CursorInvocationResult
from ..utils.cache import SimpleCache
from ..utils.concurrency import run_in_thread
from ..utils.validators import ensure_safe_path

_CACHE = SimpleCache[str, CursorInvocationResult](maxsize=32, ttl=120.0)


def _serialize_request(request: CursorInvocationRequest) -> str:
    payload = {
        "prompt": request.prompt,
        "file_path": str(request.file_path) if request.file_path else None,
        "apply_changes": request.apply_changes,
        "extra_args": request.extra_args,
    }
    return json.dumps(payload, sort_keys=True)


async def run_cursor(request: CursorInvocationRequest) -> CursorInvocationResult:
    config = get_config()
    binary = config.cursor_binary or "cursor"
    if shutil.which(binary) is None:
        raise CursorError(f"Cursor binary '{binary}' was not found in PATH")

    cache_key = _serialize_request(request)
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached

    command = [binary, "--quiet", "--format", "json"]
    if request.file_path is not None:
        safe_path = ensure_safe_path(request.file_path)
        command.extend(["--path", str(safe_path)])
    if request.apply_changes:
        command.append("--apply")
    command.extend(["--prompt", request.prompt])
    for key, value in request.extra_args.items():
        command.extend([f"--{key.replace('_', '-')}", str(value)])

    def _runner() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

    completed = await run_in_thread(_runner)
    if completed.returncode != 0:
        raise CursorError(completed.stderr.strip() or "Cursor invocation failed")

    suggestions: Dict[str, object] = {}
    if completed.stdout.strip():
        try:
            suggestions = json.loads(completed.stdout)
        except json.JSONDecodeError:
            suggestions = {"raw": completed.stdout}

    result = CursorInvocationResult(
        stdout=completed.stdout,
        stderr=completed.stderr,
        return_code=completed.returncode,
        suggestions=suggestions,
    )
    _CACHE.set(cache_key, result)
    return result


def clear_cache() -> None:
    _CACHE.clear()
