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
from .reports import generate_macro_review
from .schema import macro_schema
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
    parser.add_argument(
        "--qa-checklist",
        metavar="MACRO",
        help="Export a QA Agent MD checklist for the specified macro.",
    )
    parser.add_argument(
        "--meta-manifest",
        metavar="MACRO",
        help="Export a Meta Agent orchestration manifest for the specified macro.",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print a metadata coverage report and exit.",
    )
    parser.add_argument(
        "--export-schema",
        action="store_true",
        help="Emit the JSON Schema describing the macro catalogue and exit.",
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

        exclusive = [
            bool(args.plan),
            bool(args.plan_json),
            bool(args.qa_checklist),
            bool(args.meta_manifest),
        ]
        if sum(1 for item in exclusive if item) > 1:
            print(
                "Error: --plan, --plan-json, --qa-checklist, and --meta-manifest cannot be combined.",
                file=sys.stderr,
            )
            return 2

        if args.list:
            for name in engine.available_macros():
                print(name)
            return 0

        if args.export_schema:
            print(json.dumps(macro_schema(), indent=2))
            return 0

        if args.report:
            macros = {name: engine.describe(name) for name in engine.available_macros()}
            review = generate_macro_review(macros)
            payload = {
                "totalMacros": review.coverage.total_macros,
                "agentCoverage": review.coverage.per_agent,
                "metadataGaps": {
                    "unassigned": review.gaps.unassigned,
                    "missingOutcomes": review.gaps.missing_outcomes,
                    "missingAcceptance": review.gaps.missing_acceptance,
                    "missingQaHooks": review.gaps.missing_qa_hooks,
                    "defaultOutcomes": review.gaps.default_outcomes,
                },
                "recommendations": review.recommendations,
            }
            print(json.dumps(payload, indent=2))
            return 0

        if args.describe:
            macro = engine.describe(args.describe)
            print(
                json.dumps(
                    {
                        "name": macro.name,
                        "expansion": macro.expansion,
                        "calls": macro.calls,
                        "ownerAgent": macro.owner_agent,
                        "outcomes": macro.outcomes,
                        "acceptanceCriteria": macro.acceptance_criteria,
                        "qaHooks": macro.qa_hooks,
                    },
                    indent=2,
                )
            )
            return 0

        if args.deps:
            deps = engine.dependencies(args.deps, recursive=not args.no_recursive)
            for item in deps:
                print(item)
            return 0

        if args.qa_checklist:
            plan = planner.build(args.qa_checklist)
            print(json.dumps(plan.to_qa_checklist(), indent=2))
            return 0

        if args.meta_manifest:
            plan = planner.build(args.meta_manifest)
            print(json.dumps(plan.to_manifest(), indent=2))
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
