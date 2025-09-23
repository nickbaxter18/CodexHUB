"""JSON Schema utilities for validating macro catalogues."""

# === Imports ===
from __future__ import annotations

from copy import deepcopy
from typing import Dict, Mapping

from .types import MacroDefinitionError

# === Types ===

MacroSchema = Dict[str, object]


# === Core Logic ===

_SCHEMA: MacroSchema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://codexhub.dev/schemas/macro-system.json",
    "title": "Macro System Catalogue",
    "type": "object",
    "additionalProperties": False,
    "patternProperties": {
        "^::[a-zA-Z0-9-]+$": {
            "type": "object",
            "required": ["expansion"],
            "additionalProperties": False,
            "properties": {
                "expansion": {"type": "string", "minLength": 1},
                "calls": {
                    "type": "array",
                    "items": {"type": "string", "pattern": "^::[a-zA-Z0-9-]+$"},
                    "default": [],
                },
                "ownerAgent": {"type": "string"},
                "outcomes": {"type": "array", "items": {"type": "string"}},
                "acceptanceCriteria": {"type": "array", "items": {"type": "string"}},
                "qaHooks": {"type": "array", "items": {"type": "string"}},
                "phase": {"type": "string"},
                "priority": {"type": "string"},
                "status": {"type": "string"},
                "estimatedDuration": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "version": {"type": "string"},
            },
        }
    },
}

_ALLOWED_FIELDS = {
    "expansion",
    "calls",
    "ownerAgent",
    "outcomes",
    "acceptanceCriteria",
    "qaHooks",
    "phase",
    "priority",
    "status",
    "estimatedDuration",
    "tags",
    "version",
}


def macro_schema() -> MacroSchema:
    """Return a copy of the macro JSON schema."""

    return deepcopy(_SCHEMA)


def validate_macro_catalog(payload: Mapping[str, object]) -> None:
    """Perform lightweight schema validation for a macro catalogue."""

    if not isinstance(payload, Mapping):
        raise MacroDefinitionError("Macro catalogue must be an object.")

    for name, body in payload.items():
        if not isinstance(name, str) or not name.startswith("::"):
            raise MacroDefinitionError("Macro names must be strings prefixed with '::'.")

        if not isinstance(body, Mapping):
            raise MacroDefinitionError(f"Macro '{name}' must be defined as an object.")

        if "expansion" not in body:
            raise MacroDefinitionError(f"Macro '{name}' must include an expansion field.")

        unexpected = set(body) - _ALLOWED_FIELDS
        if unexpected:
            raise MacroDefinitionError(
                f"Macro '{name}' includes unsupported fields: {sorted(unexpected)}"
            )


# === Exports ===
__all__ = ["macro_schema", "validate_macro_catalog"]
