"""Unified command line interface for Cursor automation workflows."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Iterable, List

from src.cursor import (
    get_auto_invoker,
    get_cursor_usage_report,
    start_cursor_auto_invocation,
    validate_cursor_compliance,
)
from src.knowledge.auto_loader import (
    get_auto_loader,
    refresh_knowledge_sources,
    start_knowledge_auto_loading,
)
from src.knowledge.brain_blocks_integration import start_brain_blocks_integration
from src.mobile.mobile_app import start_mobile_app


async def _run_start(
    *,
    watch: Iterable[Path],
    include_knowledge: bool,
    include_mobile: bool,
    include_brain_blocks: bool,
    stay_alive: bool,
) -> int:
    """Start the requested Cursor subsystems."""

    tasks: List[asyncio.Task[None]] = []

    async def _start_auto_invocation() -> None:
        await start_cursor_auto_invocation(list(watch))

    tasks.append(asyncio.create_task(_start_auto_invocation()))

    if include_knowledge:
        tasks.append(asyncio.create_task(start_knowledge_auto_loading()))

    if include_mobile:
        tasks.append(asyncio.create_task(start_mobile_app()))

    if include_brain_blocks:
        tasks.append(asyncio.create_task(start_brain_blocks_integration()))

    await asyncio.gather(*tasks)

    if stay_alive:
        # Keep the process alive so background watchers continue to run.
        await asyncio.Event().wait()

    return 0


async def _run_knowledge_refresh() -> int:
    auto_loader = get_auto_loader()
    before = {source.name: source.document_count for source in auto_loader.sources}
    await refresh_knowledge_sources()
    after = {source.name: source.document_count for source in auto_loader.sources}
    print(
        json.dumps(
            {
                "refreshed_sources": after,
                "previous_counts": before,
            },
            indent=2,
        )
    )
    return 0


def _run_validate() -> int:
    compliant = validate_cursor_compliance()
    print("COMPLIANT" if compliant else "NON_COMPLIANT")
    return 0 if compliant else 1


def _run_status() -> int:
    report = get_cursor_usage_report()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("compliance_status") == "COMPLIANT" else 1


async def _run_rules() -> int:
    invoker = get_auto_invoker()
    print(json.dumps(invoker.get_rule_stats(), indent=2, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Start Cursor automation services")
    start_parser.add_argument(
        "--watch",
        action="append",
        type=Path,
        help="Workspace paths to watch for auto invocation (defaults to current repository)",
    )
    start_parser.add_argument(
        "--with-knowledge",
        action="store_true",
        help="Also start the knowledge ingestion subsystem",
    )
    start_parser.add_argument(
        "--with-mobile",
        action="store_true",
        help="Also start the mobile control subsystem",
    )
    start_parser.add_argument(
        "--with-brain-blocks",
        action="store_true",
        help="Also start the brain blocks integration",
    )
    start_parser.add_argument(
        "--stay-alive",
        action="store_true",
        help="Keep the process alive after booting subsystems",
    )

    subparsers.add_parser("validate", help="Validate Cursor compliance")
    subparsers.add_parser("status", help="Display the latest Cursor usage report")
    subparsers.add_parser("rules", help="Inspect auto-invocation rule statistics")
    subparsers.add_parser("knowledge-refresh", help="Force a reload of knowledge sources")

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "start":
        watch = args.watch or [Path.cwd()]
        return asyncio.run(
            _run_start(
                watch=watch,
                include_knowledge=args.with_knowledge,
                include_mobile=args.with_mobile,
                include_brain_blocks=args.with_brain_blocks,
                stay_alive=args.stay_alive,
            )
        )

    if args.command == "validate":
        return _run_validate()

    if args.command == "status":
        return _run_status()

    if args.command == "rules":
        return asyncio.run(_run_rules())

    if args.command == "knowledge-refresh":
        return asyncio.run(_run_knowledge_refresh())

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
