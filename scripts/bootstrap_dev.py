"""Unified bootstrap script for mixed Node/Python development environments."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence
from venv import EnvBuilder


def _run(cmd: Sequence[str], *, env: dict[str, str] | None = None) -> None:
    display = " ".join(cmd)
    print(f"→ {display}")
    subprocess.run(cmd, check=True, env=env)


def _ensure_virtualenv(venv_path: Path) -> Path:
    if not venv_path.exists():
        print(f"Creating virtual environment at {venv_path}")
        EnvBuilder(with_pip=True, clear=False, upgrade=True).create(str(venv_path))

    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def _bootstrap_node(*, frozen: bool) -> None:
    args = ["pnpm", "install"]
    if frozen:
        args.append("--frozen-lockfile")
    _run(args)
    _run(["pnpm", "exec", "husky", "install"])


def _bootstrap_python(venv_path: Path, *, extras: bool) -> None:
    python = _ensure_virtualenv(venv_path)
    _run([str(python), "-m", "pip", "install", "-r", "requirements.txt"])
    if extras:
        _run([str(python), "-m", "pip", "install", "-r", "requirements-dev.txt"])
    _run([str(python), "-m", "pre_commit", "install"])


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-node",
        action="store_true",
        help="Skip pnpm dependency installation",
    )
    parser.add_argument(
        "--skip-python",
        action="store_true",
        help="Skip Python environment setup",
    )
    parser.add_argument(
        "--venv",
        type=Path,
        default=Path(".venv"),
        help="Location for the managed virtual environment",
    )
    parser.add_argument(
        "--no-dev-extras",
        action="store_true",
        help="Install only runtime Python dependencies",
    )
    parser.add_argument(
        "--no-frozen-lockfile",
        action="store_true",
        help="Allow pnpm to update the lockfile during install",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.skip_node:
        _bootstrap_node(frozen=not args.no_frozen_lockfile)

    if not args.skip_python:
        _bootstrap_python(args.venv, extras=not args.no_dev_extras)

    print("Bootstrap complete ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
