#!/usr/bin/env python
"""Detect the highest completed build stage for RentalOS-AI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DETECTOR_PATH = Path(__file__).resolve()
SKIP_PARTS = {".git", ".mypy_cache", "node_modules", "__pycache__"}

STAGE_MARKERS = {
    1: "Stage 1 complete",
    2: "Stage 2 complete",
    3: "Stage 3 complete",
}


def should_skip(path: Path) -> bool:
    return any(part in SKIP_PARTS for part in path.parts)


def scan_for_todo(paths: Iterable[Path]) -> bool:
    for path in paths:
        if path == DETECTOR_PATH or should_skip(path):
            continue
        if path.suffix.lower() not in {".py", ".md", ".tsx", ".ts", ".json", ".yml", ".yaml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "TODO" in text:
            return True
    return False


def read_stage_marker(project_root: Path) -> int:
    changelog = project_root / "deploy_logs" / "changelog.md"
    if not changelog.exists():
        return 0
    text = changelog.read_text(encoding="utf-8").lower()
    stage = 0
    for level, marker in STAGE_MARKERS.items():
        if marker.lower() in text:
            stage = max(stage, level)
    return stage


def detect_stage(project_root: Path) -> int:
    if not project_root.exists():
        return 0
    stage = read_stage_marker(project_root)
    todo_found = scan_for_todo(project_root.rglob("*"))
    if todo_found:
        print("⚠️ TODO markers detected. Treating current stage as incomplete.", file=sys.stderr)
        return max(stage - 1, 0)
    return stage


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect RentalOS-AI build stage")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Project root path")
    args = parser.parse_args()

    project_root = args.root
    if not project_root.exists():
        print("0")
        return 0

    stage = detect_stage(project_root)
    print(stage)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
