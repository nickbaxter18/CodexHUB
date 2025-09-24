"""Unified bootstrap script for mixed Node/Python development environments."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence
from venv import EnvBuilder

STATE_FILE = Path(".cache/bootstrap_state.json")


def _load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {}
    try:
        with STATE_FILE.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        return {}


def _save_state(state: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _hash_files(paths: Sequence[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.as_posix().encode("utf-8"))
        if path.exists():
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
    return digest.hexdigest()


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


def _node_fingerprint() -> str:
    return _hash_files([Path("package.json"), Path("pnpm-lock.yaml")])


def _should_skip_node(state: dict[str, Any] | None, fingerprint: str) -> bool:
    if state is None:
        return False
    if state.get("fingerprint") != fingerprint:
        return False
    return Path("node_modules").exists()


def _bootstrap_node(*, frozen: bool, state: dict[str, Any] | None) -> dict[str, Any]:
    fingerprint = _node_fingerprint()
    if _should_skip_node(state, fingerprint):
        print("Node dependencies already up to date – skipping pnpm install")
        return {"fingerprint": fingerprint, "frozen": frozen}

    args = ["pnpm", "install"]
    if frozen:
        args.append("--frozen-lockfile")
    _run(args)
    _run(["pnpm", "exec", "husky", "install"])
    return {"fingerprint": fingerprint, "frozen": frozen}


def _python_fingerprint(*, extras: bool) -> str:
    files = [Path("requirements.txt")]
    if extras:
        files.append(Path("requirements-dev.txt"))
    return _hash_files(files)


def _should_skip_python(
    state: dict[str, Any] | None,
    fingerprint: str,
    venv_path: Path,
    *,
    extras: bool,
) -> bool:
    if state is None:
        return False
    if state.get("fingerprint") != fingerprint or state.get("extras") != extras:
        return False
    if os.name == "nt":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"
    return python_path.exists()


def _bootstrap_python(
    venv_path: Path, *, extras: bool, state: dict[str, Any] | None
) -> dict[str, Any]:
    fingerprint = _python_fingerprint(extras=extras)
    if _should_skip_python(state, fingerprint, venv_path, extras=extras):
        print("Python environment already up to date – skipping pip installs")
        return {"fingerprint": fingerprint, "extras": extras}

    python = _ensure_virtualenv(venv_path)
    _run([str(python), "-m", "pip", "install", "-r", "requirements.txt"])
    if extras:
        _run([str(python), "-m", "pip", "install", "-r", "requirements-dev.txt"])
    _run([str(python), "-m", "pre_commit", "install"])
    return {"fingerprint": fingerprint, "extras": extras}


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
    state = _load_state()
    updated_state = dict(state)

    if not args.skip_node:
        updated_state["node"] = _bootstrap_node(
            frozen=not args.no_frozen_lockfile,
            state=state.get("node"),
        )

    if not args.skip_python:
        updated_state["python"] = _bootstrap_python(
            args.venv,
            extras=not args.no_dev_extras,
            state=state.get("python"),
        )

    if updated_state != state:
        _save_state(updated_state)

    print("Bootstrap complete ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
