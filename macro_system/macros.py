"""Utilities for loading macro definitions from JSON."""

# === Imports ===
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Mapping

from .schema import validate_macro_catalog
from .types import Macro, MacroDefinitionError

# === Implementation ===

def load_macros(source: Mapping[str, object] | str | Path) -> Dict[str, Macro]:
    """Load and validate macros from a JSON file or mapping."""

    if isinstance(source, (str, Path)):
        data = _load_json(Path(source))
    else:
        data = dict(source)

    validate_macro_catalog(data)

    macros: Dict[str, Macro] = {}
    for name, payload in data.items():
        macros[name] = _convert_macro(name, payload)
    return macros


# === Error Handling ===

def _load_json(path: Path) -> Dict[str, object]:
    """Read JSON file from disk."""

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - explicit error passthrough
        raise MacroDefinitionError(f"Macro definition file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MacroDefinitionError(f"Invalid JSON in macro definition file: {path}") from exc


def _convert_macro(name: str, payload: object) -> Macro:
    """Validate and convert a raw payload into a :class:`Macro`."""

    if not isinstance(payload, dict):
        raise MacroDefinitionError(f"Macro '{name}' must be defined as an object.")

    if not isinstance(name, str) or not name.startswith("::"):
        raise MacroDefinitionError("Macro names must be strings prefixed with '::'.")

    expansion = payload.get("expansion")
    calls = payload.get("calls", [])
    owner_agent = payload.get("ownerAgent")
    outcomes = payload.get("outcomes", [])
    acceptance_criteria = payload.get("acceptanceCriteria", [])
    qa_hooks = payload.get("qaHooks", [])
    phase = payload.get("phase")
    priority = payload.get("priority")
    status = payload.get("status")
    estimated_duration = payload.get("estimatedDuration")
    tags = payload.get("tags", [])
    version = payload.get("version")

    if not isinstance(expansion, str) or not expansion.strip():
        raise MacroDefinitionError(f"Macro '{name}' must include a non-empty expansion string.")

    if not isinstance(calls, list) or not _all_strings(calls):
        raise MacroDefinitionError(f"Macro '{name}' calls must be a list of macro names.")

    if any(not item.startswith("::") for item in calls):
        raise MacroDefinitionError(
            f"Macro '{name}' calls contain an entry that is not a macro name."
        )

    if owner_agent is not None and not isinstance(owner_agent, str):
        raise MacroDefinitionError(
            f"Macro '{name}' ownerAgent must be a string when provided."
        )

    for optional_field, value in (
        ("phase", phase),
        ("priority", priority),
        ("status", status),
        ("estimatedDuration", estimated_duration),
        ("version", version),
    ):
        if value is not None and not isinstance(value, str):
            raise MacroDefinitionError(
                f"Macro '{name}' field '{optional_field}' must be a string when provided."
            )

    for field_name, value in (
        ("outcomes", outcomes),
        ("acceptanceCriteria", acceptance_criteria),
        ("qaHooks", qa_hooks),
        ("tags", tags),
    ):
        if not isinstance(value, list) or not _all_strings(value):
            raise MacroDefinitionError(
                f"Macro '{name}' field '{field_name}' must be a list of strings."
            )

    return Macro(
        name=name,
        expansion=expansion,
        calls=list(calls),
        owner_agent=owner_agent,
        outcomes=list(outcomes),
        acceptance_criteria=list(acceptance_criteria),
        qa_hooks=list(qa_hooks),
        phase=phase,
        priority=priority,
        status=status,
        estimated_duration=estimated_duration,
        tags=list(tags),
        version=version,
    )


# === Performance ===

def _all_strings(values: Iterable[object]) -> bool:
    """Return True if all values are strings."""

    return all(isinstance(item, str) for item in values)


# === Exports ===
__all__ = ["load_macros"]
