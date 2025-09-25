#!/usr/bin/env python3
"""Append an AI review decision to results/ai-review/log.json."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = ROOT / "results" / "ai-review" / "log.json"


def load_log() -> list:
    if not LOG_PATH.exists():
        return []
    with LOG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_log(entries: list) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("w", encoding="utf-8") as handle:
        json.dump(entries, handle, indent=2)
        handle.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agent",
        required=True,
        help="Agent role submitting the review (e.g. cursor, human).",
    )
    parser.add_argument("--source", required=True, help="Triggering workflow or script.")
    parser.add_argument("--summary", required=True, help="Short description of the review outcome.")
    parser.add_argument("--accepted", type=int, default=0, help="Number of accepted suggestions.")
    parser.add_argument("--rejected", type=int, default=0, help="Number of rejected suggestions.")
    parser.add_argument("--notes", help="Optional detailed notes.")
    args = parser.parse_args(argv)

    entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "agent": args.agent,
        "source": args.source,
        "summary": args.summary,
        "accepted": args.accepted,
        "rejected": args.rejected,
        "notes": args.notes,
    }

    entries = load_log()
    entries.append(entry)
    write_log(entries)
    print(f"Logged AI review decision to {LOG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
