"""Header & Purpose: ergonomic CLI gateway for the macro system."""

from __future__ import annotations

# === Imports / Dependencies ===
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List

from .orchestrator import MacroOrchestrator
from .planner import MacroPlanner
from .repository import MacroRepository
from .types import MacroError

# === Types / Interfaces / Schemas ===
# CLI arguments map to engine and planner operations.


# === Core Logic / Implementation ===
def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Expand, audit, and plan macros from macros.json",
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
        default=Path(__file__).resolve().with_name("macros.json"),
        help="Path to macros.json (defaults to bundled file).",
    )
    parser.add_argument(
        "--catalog",
        dest="catalogs",
        action="append",
        type=Path,
        metavar="PATH",
        help="Additional macro catalogue JSON file(s) to merge.",
    )
    parser.add_argument(
        "--catalog-dir",
        dest="catalog_dirs",
        action="append",
        type=Path,
        metavar="DIR",
        help="Load all *.json catalogues from DIR and merge them.",
    )
    parser.add_argument(
        "--no-default",
        action="store_true",
        help="Skip loading the bundled macros.json file.",
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
        "--ancestors",
        metavar="MACRO",
        help="Show macros that depend on the specified macro.",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="When used with --deps or --ancestors, only show direct relationships.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the macro graph before running other commands.",
    )
    parser.add_argument(
        "--validate-strict",
        action="store_true",
        help="Run strict validation including entrypoint reachability checks.",
    )
    parser.add_argument(
        "--entrypoint",
        action="append",
        dest="entrypoints",
        metavar="MACRO",
        help="Specify entrypoint(s) for auditing and strict validation.",
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
        "--markdown",
        metavar="MACRO",
        help="Render the macro plan as Markdown.",
    )
    parser.add_argument(
        "--tasks",
        metavar="MACRO",
        help="List the actionable tasks for the macro.",
    )
    parser.add_argument(
        "--assign-agents",
        metavar="MACRO",
        help="Group MACRO's tasks by agent roles using metadata heuristics.",
    )
    parser.add_argument(
        "--assign-json",
        metavar="MACRO",
        help="Output agent assignments for MACRO as JSON.",
    )
    parser.add_argument(
        "--assign-prompts",
        metavar="MACRO",
        nargs="+",
        help="Emit agent-specific prompts for the provided MACRO(s).",
    )
    parser.add_argument(
        "--assign-prompts-format",
        default="prompt",
        choices=["prompt", "outline", "text"],
        help="Select output style when using --assign-prompts (default: prompt).",
    )
    parser.add_argument(
        "--assign-include-non-leaf",
        action="store_true",
        help="Include parent macros when generating agent assignments.",
    )
    parser.add_argument(
        "--agent-map",
        action="append",
        metavar="DOMAIN=AGENT",
        help="Override domain-to-agent mappings for orchestration.",
    )
    parser.add_argument(
        "--search",
        metavar="QUERY",
        help="Search macros by name, expansion text, or metadata.",
    )
    parser.add_argument(
        "--filter-meta",
        action="append",
        metavar="KEY=VALUE",
        help=(
            "Filter macros by metadata key/value pairs. Provide multiple values to "
            "apply additional filters."
        ),
    )
    parser.add_argument(
        "--group-meta",
        metavar="KEY",
        help="Group macros by a metadata key and output JSON mapping values to macros.",
    )
    parser.add_argument(
        "--match-any",
        action="store_true",
        help="When filtering metadata, match macros satisfying any filter instead of all.",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Treat metadata comparisons as case-sensitive.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show catalogue statistics and exit.",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Run a full audit and emit JSON describing catalogue health.",
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="List merged catalogue sources and exit.",
    )
    parser.add_argument(
        "--export-merged",
        type=Path,
        metavar="DEST",
        help="Write the merged catalogue to DEST as JSON.",
    )
    parser.add_argument(
        "--path",
        nargs=2,
        metavar=("SOURCE", "TARGET"),
        help="Explain the dependency path from SOURCE to TARGET if it exists.",
    )
    parser.add_argument(
        "--trace",
        metavar="MACRO",
        help="Expand a macro while displaying the traversal trace.",
    )
    parser.add_argument(
        "--context",
        action="append",
        metavar="KEY=VALUE",
        help=(
            "Provide placeholder substitution values using KEY=VALUE pairs. "
            "Repeat for multiple entries."
        ),
    )
    parser.add_argument(
        "--context-file",
        type=Path,
        help="Load placeholder substitutions from a JSON object file.",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Allow rendering to succeed when some placeholders remain unresolved.",
    )
    parser.add_argument(
        "--placeholders",
        metavar="MACRO",
        help=(
            "List placeholder tokens (e.g. {{name}}) referenced by the macro. "
            "Includes dependencies by default."
        ),
    )
    parser.add_argument(
        "--placeholders-direct",
        action="store_true",
        help="When listing placeholders, only show those defined on the macro itself.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    """Entry point for the macro-system CLI."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        repository = _build_repository(args, parser)
        engine = repository.engine()
        planner = MacroPlanner(engine)

        try:
            agent_overrides = (
                _parse_agent_map(args.agent_map) if args.agent_map else None
            )
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

        orchestrator = MacroOrchestrator(engine, agent_map=agent_overrides)

        if args.validate:
            engine.validate()

        if args.validate_strict:
            engine.validate_strict(entrypoints=args.entrypoints)

        additional_flags: List[bool] = [
            args.list,
            bool(args.describe),
            bool(args.deps),
            bool(args.ancestors),
            args.stats,
            args.audit,
            bool(args.search),
            bool(args.filter_meta),
            bool(args.group_meta),
            bool(args.plan),
            bool(args.plan_json),
            bool(args.markdown),
            bool(args.tasks),
            bool(args.path),
            bool(args.trace),
            bool(args.placeholders),
            bool(args.assign_agents),
            bool(args.assign_json),
            bool(args.assign_prompts),
        ]
        has_followup = bool(args.macro) or any(additional_flags)

        if args.list_sources:
            for source in repository.sources():
                print(source)
            if not has_followup and not args.export_merged:
                return 0

        if args.export_merged:
            repository.export(args.export_merged)
            print(
                json.dumps(
                    {
                        "export": str(args.export_merged),
                        "total_macros": len(repository),
                        "sources": repository.sources(),
                    },
                    indent=2,
                )
            )
            if not has_followup:
                return 0

        multi_plan_flags: List[str | None] = [
            args.plan,
            args.plan_json,
            args.markdown,
        ]
        selected = [flag for flag in multi_plan_flags if flag]
        if len(selected) > 1:
            print(
                "Error: only one of --plan, --plan-json, or --markdown may be used at a time.",
                file=sys.stderr,
            )
            return 2

        try:
            context: Dict[str, object] = {}
            if args.context_file:
                context.update(_load_context_file(args.context_file))
            if args.context:
                context.update(_parse_context_pairs(args.context))
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

        if args.stats:
            stats = engine.stats()
            print(json.dumps(stats.to_dict(), indent=2))
            return 0

        if args.audit:
            audit = engine.audit(entrypoints=args.entrypoints)
            print(json.dumps(audit.to_dict(), indent=2))
            return 0

        if args.placeholders:
            placeholders = engine.placeholders(
                args.placeholders, recursive=not args.placeholders_direct
            )
            for name in placeholders:
                print(name)
            return 0

        if args.group_meta:
            grouped = engine.group_by_metadata(
                args.group_meta, case_sensitive=args.case_sensitive
            )
            payload = {
                value: [macro.name for macro in macros]
                for value, macros in grouped.items()
            }
            print(json.dumps(payload, indent=2))
            return 0

        if args.filter_meta:
            try:
                filters = _parse_filters(args.filter_meta)
            except ValueError as exc:
                print(f"Error: {exc}", file=sys.stderr)
                return 2
            matches = engine.filter_by_metadata(
                filters,
                case_sensitive=args.case_sensitive,
                match_all=not args.match_any,
            )
            for macro in matches:
                print(macro.name)
            return 0

        if args.search:
            matches = engine.search(args.search)
            for macro in matches:
                print(macro.name)
            return 0

        if args.list:
            for name in engine.available_macros():
                print(name)
            return 0

        if args.describe:
            macro = engine.describe(args.describe)
            print(json.dumps(macro.describe(), indent=2))
            return 0

        if args.deps:
            deps = engine.dependencies(
                args.deps, recursive=not args.no_recursive
            )
            for item in deps:
                print(item)
            return 0

        if args.ancestors:
            parents = engine.ancestors(
                args.ancestors, recursive=not args.no_recursive
            )
            for parent in parents:
                print(parent)
            return 0

        if args.path:
            source, target = args.path
            path = engine.explain_path(source, target)
            if not path:
                print(
                    f"No dependency path found from {source} to {target}.",
                    file=sys.stderr,
                )
                return 1
            print(" -> ".join(path))
            return 0

        if args.plan_json:
            print(planner.render_json(args.plan_json))
            return 0

        if args.plan:
            print(planner.render_outline(args.plan))
            return 0

        if args.markdown:
            print(planner.render_markdown(args.markdown))
            return 0

        if args.tasks:
            for task in planner.tasks(args.tasks):
                print(task)
            return 0

        include_non_leaf = args.assign_include_non_leaf
        if args.assign_prompts:
            try:
                payload = orchestrator.dispatch(
                    args.assign_prompts,
                    include_non_leaf=include_non_leaf,
                    format=args.assign_prompts_format,
                )
            except ValueError as exc:
                print(f"Error: {exc}", file=sys.stderr)
                return 2

            formatter = args.assign_prompts_format.casefold()
            for index, (agent, content) in enumerate(payload.items()):
                if index:
                    print()
                if formatter in {"text", "instructions"}:
                    print(f"## {agent}\n")
                print(content)
            return 0

        if args.assign_json:
            assignments = orchestrator.assign(
                args.assign_json, include_non_leaf=include_non_leaf
            )
            payload = [assignment.to_dict() for assignment in assignments]
            print(json.dumps(payload, indent=2))
            return 0

        if args.assign_agents:
            assignments = orchestrator.assign(
                args.assign_agents, include_non_leaf=include_non_leaf
            )
            for index, assignment in enumerate(assignments):
                if index:
                    print()
                print(assignment.to_outline())
            return 0

        if args.trace:
            expansion, trace = engine.expand_with_trace(args.trace)
            print("# Trace")
            for item in trace:
                print(f"- {item}")
            print("\n# Expansion\n")
            if context:
                try:
                    expansion = engine.render_text(
                        expansion, context, strict=not args.allow_partial
                    )
                except MacroError as exc:
                    print(f"Error: {exc}", file=sys.stderr)
                    return 1
            print(expansion)
            return 0

        if not args.macro:
            parser.print_help()
            return 0

        if context:
            try:
                result = engine.render_many(
                    args.macro, context, strict=not args.allow_partial
                )
            except MacroError as exc:
                print(f"Error: {exc}", file=sys.stderr)
                return 1
        else:
            result = engine.expand_many(args.macro)
        if args.output:
            args.output.write_text(result, encoding="utf-8")
        else:
            print(result)
        return 0
    except MacroError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


# === Error & Edge Handling ===
# Exceptions are surfaced with user-friendly messages via stderr.


# === Performance Considerations ===
# CLI delegates heavy lifting to the cached engine and planner implementations.


# === Supporting Utilities ===
def _parse_filters(pairs: Iterable[str]) -> Dict[str, str]:
    """Parse ``KEY=VALUE`` strings into a dictionary of metadata filters."""

    filters: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(
                "Metadata filters must be provided as KEY=VALUE expressions."
            )
        key, value = pair.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise ValueError("Metadata filter keys and values must be non-empty.")
        if key in filters and filters[key] != value:
            raise ValueError(
                f"Metadata key '{key}' was provided more than once with different values."
            )
        filters[key] = value
    return filters


def _parse_context_pairs(pairs: Iterable[str]) -> Dict[str, object]:
    """Parse KEY=VALUE pairs into a context mapping."""

    context: Dict[str, object] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError("Context values must be provided as KEY=VALUE pairs.")
        key, value = pair.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("Context keys must be non-empty strings.")
        context[key] = value.strip()
    return context


def _parse_agent_map(pairs: Iterable[str]) -> Dict[str, str]:
    """Parse DOMAIN=AGENT expressions for orchestrator overrides."""

    mapping: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError("Agent mappings must use the form DOMAIN=AGENT.")
        domain, agent = pair.split("=", 1)
        domain = domain.strip().casefold()
        agent = agent.strip()
        if not domain or not agent:
            raise ValueError("Agent mapping domains and agents must be non-empty.")
        mapping[domain] = agent
    return mapping


def _load_context_file(path: Path) -> Dict[str, object]:
    """Load context substitutions from a JSON file containing an object."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - user-supplied path
        raise ValueError(f"Context file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Context file contains invalid JSON: {path}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Context file must define a JSON object mapping names to values.")

    context: Dict[str, object] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            raise ValueError("Context file keys must be strings.")
        context[key] = value
    return context


def _build_repository(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> MacroRepository:
    """Construct a macro repository from CLI arguments."""

    sources: List[Path | Dict[str, object]] = []
    if not args.no_default:
        sources.append(args.file)
    if args.catalogs:
        sources.extend(args.catalogs)
    if args.catalog_dirs:
        for directory in args.catalog_dirs:
            if not directory.exists():
                parser.error(f"Catalogue directory not found: {directory}")
            if not directory.is_dir():
                parser.error(f"Catalogue directory must be a directory: {directory}")
            sources.extend(
                sorted(
                    candidate
                    for candidate in directory.glob("*.json")
                    if candidate.is_file()
                )
            )

    if not sources:
        parser.error(
            "No macro catalogues supplied. Provide --catalog/--catalog-dir or remove --no-default."
        )

    return MacroRepository(sources=sources)


# === Exports / Public API ===
__all__ = ["main", "build_parser"]


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
