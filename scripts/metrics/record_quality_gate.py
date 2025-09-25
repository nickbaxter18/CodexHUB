#!/usr/bin/env python3
"""Append quality gate execution metadata to the metrics ledger."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
from pathlib import Path
from typing import List, Sequence

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "results" / "metrics"
LOG_PATH = RESULTS_DIR / "quality-gates-log.ndjson"
LATEST_PATH = RESULTS_DIR / "quality-gates-latest.json"


def decode_command(entry: str) -> dict:
    encoded, start, end, exit_code = entry.split(":", 3)
    label = base64.b64decode(encoded.encode("utf-8")).decode("utf-8")
    start_ts = dt.datetime.fromtimestamp(int(start), tz=dt.timezone.utc)
    end_ts = dt.datetime.fromtimestamp(int(end), tz=dt.timezone.utc)
    return {
        "command": label,
        "startedAt": start_ts.isoformat() + "Z",
        "endedAt": end_ts.isoformat() + "Z",
        "durationSeconds": (end_ts - start_ts).total_seconds(),
        "exitCode": int(exit_code),
    }


def write_entry(entry: dict) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry))
        handle.write("\n")
    with LATEST_PATH.open("w", encoding="utf-8") as handle:
        json.dump(entry, handle, indent=2)
        handle.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--exit-code", type=int, required=True)
    parser.add_argument("--started-at", type=int, required=True, help="Unix timestamp (seconds).")
    parser.add_argument("--ended-at", type=int, required=True, help="Unix timestamp (seconds).")
    parser.add_argument("--command-entry", action="append", default=[])
    parser.add_argument("--failed-command")
    args = parser.parse_args(argv)

    started_at = dt.datetime.fromtimestamp(args.started_at, tz=dt.timezone.utc)
    ended_at = dt.datetime.fromtimestamp(args.ended_at, tz=dt.timezone.utc)

    commands: List[dict] = [decode_command(entry) for entry in args.command_entry]

    payload = {
        "stage": args.stage,
        "exitCode": args.exit_code,
        "startedAt": started_at.isoformat() + "Z",
        "endedAt": ended_at.isoformat() + "Z",
        "durationSeconds": (ended_at - started_at).total_seconds(),
        "commands": commands,
        "failedCommand": (
            base64.b64decode(args.failed_command).decode("utf-8") if args.failed_command else None
        ),
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
    }

    write_entry(payload)
    print(f"Recorded quality gate execution at {LOG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
