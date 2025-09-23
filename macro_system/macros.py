"""Utilities for loading macro definitions from JSON."""

# === Imports ===
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Mapping

from .types import Macro, MacroDefinitionError

# === Implementation ===

def load_macros(source: Mapping[str, object] | str | Path) -> Dict[str, Macro]:
    """Load and validate macros from a JSON file or mapping."""

    if isinstance(source, (str, Path)):
        data = _load_json(Path(source))
    else:
        data = dict(source)

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

    if not isinstance(expansion, str) or not expansion.strip():
        raise MacroDefinitionError(f"Macro '{name}' must include a non-empty expansion string.")

    if not isinstance(calls, list) or not _all_strings(calls):
        raise MacroDefinitionError(f"Macro '{name}' calls must be a list of macro names.")

    return Macro(name=name, expansion=expansion, calls=list(calls))


# === Performance ===

def _all_strings(values: Iterable[object]) -> bool:
    """Return True if all values are strings."""

    return all(isinstance(item, str) for item in values)


# === Exports ===
__all__ = ["load_macros"]
