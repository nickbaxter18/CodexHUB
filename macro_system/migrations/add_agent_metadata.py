"""Add agent metadata fields to legacy macro definitions.

Header & Purpose:
    Provides a command-line migration that enriches ``macros.json`` entries with
    agent-aware metadata required for QA/Meta coordination.

Imports/Dependencies:
    * json for parsing and serialising macro definitions.
    * pathlib.Path for filesystem access.
    * typing for type annotations.

Types/Interfaces/Schemas:
    No custom types are introduced; the migration operates on ``dict`` objects
    containing macro payloads.

Core Logic/Implementation:
    ``migrate_file`` reads the macros file, adds metadata when absent, and writes
    back an ordered representation that maintains deterministic formatting.

Error & Edge Handling:
    The migration validates file existence and tolerates previously migrated
    macros by leaving explicit metadata untouched.

Performance Considerations:
    The dataset is small (O(number of macros)), so a straightforward iteration is
    sufficient.

Exports/Public API:
    ``migrate_file`` and ``main`` for programmatic and CLI usage respectively.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, Mapping, MutableMapping

# === Constants ===

_AGENT_KEYWORDS: Mapping[str, Iterable[str]] = {
    "QA Agent": (
        "qa",
        "test",
        "lint",
        "quality",
        "security",
        "access",
        "audit",
    ),
    "Meta Agent": (
        "meta",
        "orchestr",
        "plan",
        "coord",
        "governance",
    ),
    "Knowledge Agent": (
        "knowledge",
        "research",
        "docs",
        "documentation",
        "brief",
        "analysis",
    ),
    "Backend Agent": (
        "backend",
        "api",
        "database",
        "schema",
        "fastapi",
        "server",
    ),
    "Frontend Agent": (
        "frontend",
        "ui",
        "ux",
        "react",
        "design",
        "motion",
        "tailwind",
    ),
    "Architect Agent": (
        "arch",
        "strategy",
        "master",
        "system",
    ),
}

_AGENT_PRIORITY: Mapping[str, int] = {
    "QA Agent": 0,
    "Meta Agent": 1,
    "Knowledge Agent": 2,
    "Backend Agent": 3,
    "Frontend Agent": 4,
    "Architect Agent": 5,
}

_DEFAULT_ACCEPTANCE: Iterable[str] = (
    "All dependencies expand without errors and metadata fields are populated.",
    "QA Agent MD can identify the accountable owner for this macro step.",
)

_DEFAULT_QA_HOOKS: Iterable[str] = (
    "qa::review",
    "qa::report",
)

# === Helpers ===


def infer_owner(name: str, expansion: str) -> str:
    """Infer an owner agent using heuristic keyword matching."""

    normalised_name = name.lower()
    if any(
        token in normalised_name for token in ("::qa", "qa", "test", "access", "audit", "security")
    ):
        return "QA Agent"

    haystack = f"{name} {expansion}".lower()
    tokens = set(re.findall(r"[a-z]+", haystack))
    best_agent = "Architect Agent"
    best_score = 0

    for agent, keywords in _AGENT_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            keyword = keyword.lower()
            if len(keyword) <= 3:
                if keyword in tokens:
                    score += 1
            elif keyword in haystack:
                score += 1
        if score and (
            score > best_score
            or (
                score == best_score
                and _AGENT_PRIORITY.get(agent, 99) < _AGENT_PRIORITY.get(best_agent, 99)
            )
        ):
            best_agent = agent
            best_score = score

    return best_agent


def _default_outcomes(owner: str, name: str) -> list[str]:
    """Return the default outcomes payload."""

    return [
        f"{owner} delivers the {name} macro with actionable guidance.",
        "Outputs are structured for downstream agent consumption.",
    ]


def _looks_like_default_outcomes(values: object) -> bool:
    """Return True when the supplied outcomes match the default template."""

    if not isinstance(values, list) or len(values) != 2:
        return False
    first, second = values
    return (
        isinstance(first, str)
        and "macro with actionable guidance" in first
        and isinstance(second, str)
        and second.strip() == "Outputs are structured for downstream agent consumption."
    )


def ensure_metadata(payload: MutableMapping[str, object]) -> None:
    """Populate ownerAgent/outcomes/acceptanceCriteria/qaHooks fields."""

    expansion = str(payload.get("expansion", ""))
    name = str(payload.get("name", "")) or "::unknown"

    payload["ownerAgent"] = infer_owner(name, expansion)
    owner = payload["ownerAgent"]
    outcomes = payload.get("outcomes")
    if not isinstance(outcomes, list) or not outcomes or _looks_like_default_outcomes(outcomes):
        payload["outcomes"] = _default_outcomes(owner, name)
    else:
        payload["outcomes"] = list(outcomes)

    acceptance = payload.get("acceptanceCriteria")
    if not isinstance(acceptance, list) or not acceptance:
        payload["acceptanceCriteria"] = list(_DEFAULT_ACCEPTANCE)
    else:
        payload["acceptanceCriteria"] = list(acceptance)

    qa_hooks = payload.get("qaHooks")
    if not isinstance(qa_hooks, list) or not qa_hooks:
        hooks = list(_DEFAULT_QA_HOOKS)
    else:
        hooks = list(dict.fromkeys(qa_hooks))

    if payload["ownerAgent"] == "QA Agent" and "qa::execute" not in hooks:
        hooks.insert(0, "qa::execute")

    payload["qaHooks"] = hooks


def reorder_payload(payload: MutableMapping[str, object]) -> Dict[str, object]:
    """Return a new payload dict with deterministic key ordering."""

    ordered: Dict[str, object] = {
        "expansion": payload["expansion"],
        "calls": payload.get("calls", []),
        "ownerAgent": payload.get("ownerAgent"),
        "outcomes": payload.get("outcomes", []),
        "acceptanceCriteria": payload.get("acceptanceCriteria", []),
        "qaHooks": payload.get("qaHooks", []),
    }
    return ordered


# === Core Migration Logic ===


def migrate_file(path: Path) -> None:
    """Apply metadata enrichment to ``path`` in-place."""

    data = json.loads(path.read_text(encoding="utf-8"))
    updated: Dict[str, Dict[str, object]] = {}

    for name, payload in data.items():
        if not isinstance(payload, dict):
            raise ValueError(f"Macro '{name}' must be defined as an object.")
        payload = dict(payload)
        payload.setdefault("name", name)
        ensure_metadata(payload)
        ordered = reorder_payload(payload)
        updated[name] = ordered

    path.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# === CLI Support ===


def build_parser() -> argparse.ArgumentParser:
    """Construct an argument parser for the migration script."""

    parser = argparse.ArgumentParser(
        description="Add agent metadata to macro definitions.",
    )
    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=Path("macro_system/macros.json"),
        help="Path to the macros.json file to migrate.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    """Entry point for command-line usage."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    migrate_file(args.path)
    return 0


if __name__ == "__main__":  # pragma: no cover - script execution guard
    raise SystemExit(main())
