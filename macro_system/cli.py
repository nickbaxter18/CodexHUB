"""Command-line interface for interacting with the macro system."""

# === Imports ===
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from .engine import MacroEngine
from .planner import MacroPlanner
from .types import MacroError


# === Implementation ===


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Expand and inspect macros from macros.json",
        prog="macro-system",
    )
    parser.add_argument(
        "macro",
        nargs="*",
        help="Macro names to expand. Accepts multiple values.",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        default=Path("macro_system/macros.json"),
        help="Path to macros.json (defaults to bundled file).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional file path to write the expansion output.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available macros and exit.",
    )
    parser.add_argument(
        "--describe",
        metavar="MACRO",
        help="Print the JSON definition for the specified macro.",
    )
    parser.add_argument(
        "--deps",
        metavar="MACRO",
        help="Show the dependency chain for the specified macro.",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="When used with --deps, only show direct dependencies.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the macro graph before running other commands.",
    )
    parser.add_argument(
        "--plan",
        metavar="MACRO",
        help="Render the macro as a nested execution plan.",
    )
    parser.add_argument(
        "--plan-json",
        metavar="MACRO",
        help="Render the macro plan as JSON for downstream tooling.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    """Entry point for the macro-system CLI."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        engine = MacroEngine.from_json(args.file)
        planner = MacroPlanner(engine)

        if args.validate:
            engine.validate()

        if args.plan and args.plan_json:
            print("Error: --plan and --plan-json cannot be used together.", file=sys.stderr)
            return 2

        if args.list:
            for name in engine.available_macros():
                print(name)
            return 0

        if args.describe:
            macro = engine.describe(args.describe)
            print(
                json.dumps(
                    {
                        "name": macro.name,
                        "expansion": macro.expansion,
                        "calls": macro.calls,
                    },
                    indent=2,
                )
            )
            return 0

        if args.deps:
            deps = engine.dependencies(
                args.deps, recursive=not args.no_recursive
            )
            for item in deps:
                print(item)
            return 0

        if args.plan_json:
            plan = planner.build(args.plan_json)
            print(json.dumps(plan.to_dict(), indent=2))
            return 0

        if args.plan:
            print(planner.render_outline(args.plan))
            return 0

        if not args.macro:
            parser.print_help()
            return 0

        result = engine.expand_many(args.macro)
        if args.output:
            args.output.write_text(result, encoding="utf-8")
        else:
            print(result)
        return 0
    except MacroError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


# === Exports ===
__all__ = ["main", "build_parser"]


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
