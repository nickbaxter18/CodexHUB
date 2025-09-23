"""Header & Purpose: load macro catalogues from JSON definitions."""

from __future__ import annotations

# === Imports / Dependencies ===
import json
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence

from .types import Macro, MacroDefinitionError

# === Types / Interfaces / Schemas ===
# Macros are represented by :class:`Macro` dataclasses defined in ``types``.

CatalogSource = Mapping[str, object] | str | Path


# === Core Logic / Implementation ===
CATALOG_FILENAME = "macros.json"


def load_macros(source: CatalogSource) -> Dict[str, Macro]:
    """Load and validate macros from a JSON file path or in-memory mapping."""

    if isinstance(source, (str, Path)):
        data = _load_json(Path(source))
    else:
        data = dict(source)

    macros: Dict[str, Macro] = {}
    for name, payload in data.items():
        macros[name] = _convert_macro(name, payload)
    return macros


def load_catalogs(sources: Sequence[CatalogSource]) -> Dict[str, Macro]:
    """Merge multiple catalogues, ensuring definitions remain unique."""

    merged: Dict[str, Macro] = {}
    for raw_source in sources:
        catalog = load_macros(raw_source)
        for name, macro in catalog.items():
            existing = merged.get(name)
            if existing is not None and existing.describe() != macro.describe():
                raise MacroDefinitionError(
                    f"Duplicate definition detected for macro '{name}' across catalogues."
                )
            merged[name] = macro
    return merged


def load_default_catalog() -> Dict[str, Macro]:
    """Load the bundled macro catalogue shipped with the package."""

    default_path = Path(__file__).with_name(CATALOG_FILENAME)
    return load_macros(default_path)


# === Error & Edge Handling ===

def _load_json(path: Path) -> Dict[str, object]:
    """Read JSON file from disk with explicit error reporting."""

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
    metadata = payload.get("metadata", {})

    if not isinstance(expansion, str) or not expansion.strip():
        raise MacroDefinitionError(f"Macro '{name}' must include a non-empty expansion string.")

    if not isinstance(calls, list) or not _all_strings(calls):
        raise MacroDefinitionError(f"Macro '{name}' calls must be a list of macro names.")

    if metadata and not isinstance(metadata, dict):
        raise MacroDefinitionError(f"Macro '{name}' metadata must be an object if provided.")

    return Macro(name=name, expansion=expansion, calls=list(calls), metadata=dict(metadata))


# === Performance Considerations ===

def _all_strings(values: Iterable[object]) -> bool:
    """Return ``True`` if all values are strings; short-circuits on first failure."""

    return all(isinstance(item, str) for item in values)


# === Exports / Public API ===
__all__ = [
    "CATALOG_FILENAME",
    "load_catalogs",
    "load_default_catalog",
    "load_macros",
]
