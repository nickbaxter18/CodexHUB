"""Smoke tests ensuring local and git hooks reference required tooling."""

from __future__ import annotations

from pathlib import Path


def test_pre_commit_config_contains_required_hooks() -> None:
    """Ensure pre-commit configuration references Python formatters and commitlint."""

    config = Path(".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "black" in config
    assert "isort" in config
    assert "commitlint" in config


def test_husky_hooks_exist() -> None:
    """Verify Husky scripts are present for pre-commit, pre-push, and commit-msg."""

    husky_dir = Path(".husky")
    for hook in ("pre-commit", "pre-push", "commit-msg"):
        path = husky_dir / hook
        assert path.exists(), f"Missing Husky hook: {hook}"
        assert path.read_text(encoding="utf-8").strip() != ""
