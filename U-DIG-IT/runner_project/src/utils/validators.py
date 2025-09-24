"""Validation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence

from ..config import get_config
from ..errors import ValidationError

_SAFE_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-/:\\")


def validate_command(command: str) -> str:
    """Ensure the command is allowed."""

    config = get_config()
    if command not in config.allowed_commands:
        raise ValidationError(f"Command '{command}' is not permitted")
    return command


def sanitize_args(args: Sequence[str]) -> List[str]:
    """Sanitize command arguments by validating characters."""

    sanitized: List[str] = []
    for arg in args:
        if not isinstance(arg, str):
            raise ValidationError("Command arguments must be strings")
        if not arg:
            raise ValidationError("Empty arguments are not allowed")
        if any(char not in _SAFE_CHARS for char in arg):
            raise ValidationError(f"Argument contains unsafe characters: {arg}")
        sanitized.append(arg)
    return sanitized


def ensure_safe_path(path: Path) -> Path:
    """Ensure the provided path resolves under the configured root."""

    config = get_config()
    resolved = path.expanduser().resolve()
    root = config.root_dir.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValidationError("Path must reside within the configured root directory") from exc
    return resolved


def ensure_safe_sequence(paths: Iterable[Path]) -> List[Path]:
    """Validate and return safe paths."""

    return [ensure_safe_path(path) for path in paths]
