#!/usr/bin/env python3
"""Collect build, test, and remediation metrics for CodexHUB."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

ROOT = Path(__file__).resolve().parents[2]
METRICS_DIR = ROOT / "results" / "metrics"
DEFAULT_COMMANDS: List[List[str]] = [
    ["pnpm", "lint"],
    ["pnpm", "test"],
    ["pnpm", "run", "typecheck"],
    ["python", "-m", "pytest"],
]


def run_command(command: List[str]) -> dict:
    start = dt.datetime.utcnow()
    proc = subprocess.run(command, capture_output=True, text=True)
    end = dt.datetime.utcnow()
    duration = (end - start).total_seconds()
    return {
        "command": command,
        "startedAt": start.isoformat() + "Z",
        "endedAt": end.isoformat() + "Z",
        "durationSeconds": duration,
        "exitCode": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
        "passed": proc.returncode == 0,
    }


def git_log(window_days: int) -> Iterable[tuple[dt.datetime, str]]:
    since = (dt.datetime.utcnow() - dt.timedelta(days=window_days)).isoformat()
    result = subprocess.run(
        [
            "git",
            "log",
            f"--since={since}",
            "--pretty=format:%H%x09%ad%x09%s",
            "--date=iso",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git log failed: {result.stderr}")

    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        _commit, date_str, message = line.split("\t", 2)
        yield dt.datetime.fromisoformat(date_str.strip()), message.strip()


def collect_git_metrics(window_days: int) -> dict:
    commits = list(git_log(window_days))
    total_commits = len(commits)
    issue_like = 0
    remediation = []

    for timestamp, message in commits:
        lowered = message.lower()
        if "issue" in lowered or "#" in message:
            issue_like += 1
        if any(keyword in lowered for keyword in ("fix", "remedi", "patch")):
            remediation.append(timestamp)

    remediation.sort()
    cadence_days = None
    if len(remediation) > 1:
        deltas = [
            (later - earlier).total_seconds() / 86400
            for earlier, later in zip(remediation, remediation[1:], strict=False)
        ]
        cadence_days = statistics.mean(deltas)

    return {
        "windowDays": window_days,
        "totalCommits": total_commits,
        "issueLikeCommits": issue_like,
        "remediationCommits": len(remediation),
        "remediationCadenceDays": cadence_days,
    }


def load_history(path: Path) -> list:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window-days", type=int, default=30)
    parser.add_argument(
        "--skip-commands",
        action="store_true",
        help="Do not execute build/test commands; only collect git metrics.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=METRICS_DIR / "latest.json",
        help="Path for the latest metrics report (default: results/metrics/latest.json).",
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=METRICS_DIR / "history.json",
        help="History file that receives appended snapshots.",
    )
    parser.add_argument(
        "--commands",
        nargs="*",
        help=(
            "Override default commands. Provide commands separated by '--'."
            " Example: --commands pnpm lint -- pnpm test"
        ),
    )

    args = parser.parse_args(argv)

    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    command_groups: List[List[str]]
    if args.commands:
        command_groups = []
        current: List[str] = []
        for token in args.commands:
            if token == "--":
                if current:
                    command_groups.append(current)
                    current = []
                continue
            current.append(token)
        if current:
            command_groups.append(current)
    else:
        command_groups = DEFAULT_COMMANDS

    command_metrics = []
    if not args.skip_commands:
        for command in command_groups:
            try:
                command_metrics.append(run_command(command))
            except FileNotFoundError as exc:
                command_metrics.append(
                    {
                        "command": command,
                        "error": f"Command not found: {exc}",
                        "passed": False,
                    }
                )

    git_metrics = collect_git_metrics(args.window_days)

    snapshot = {
        "generatedAt": dt.datetime.utcnow().isoformat() + "Z",
        "commandMetrics": command_metrics,
        "gitMetrics": git_metrics,
    }

    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, indent=2)

    history = load_history(args.history)
    history.append(snapshot)
    with args.history.open("w", encoding="utf-8") as handle:
        json.dump(history, handle, indent=2)

    print(f"Metrics written to {args.output}")
    print(f"History updated at {args.history}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
