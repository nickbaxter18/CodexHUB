"""Header & Purpose: tests for macro repository catalogue management."""

from __future__ import annotations

# === Imports / Dependencies ===
import json
from pathlib import Path

import pytest

from macro_system.Macros.repository import MacroRepository
from macro_system.Macros.types import MacroDefinitionError


# === Types / Interfaces / Schemas ===
# Tests operate on dictionaries and paths compatible with CatalogSource alias.


# === Core Logic / Implementation ===
def test_repository_merges_sources_and_exports(tmp_path: Path) -> None:
    """Repository merges in-memory and file-backed catalogues."""

    base_catalog = {
        "::alpha": {"expansion": "Alpha", "calls": []},
    }
    extra_path = tmp_path / "extra.json"
    extra_path.write_text(
        json.dumps({"::beta": {"expansion": "Beta", "calls": []}}),
        encoding="utf-8",
    )

    repository = MacroRepository([base_catalog, extra_path])
    macros = repository.macros()
    assert set(macros) == {"::alpha", "::beta"}

    export_path = tmp_path / "merged.json"
    repository.export(export_path)
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert payload["::alpha"]["expansion"] == "Alpha"
    assert payload["::beta"]["expansion"] == "Beta"


def test_repository_rejects_empty_sources() -> None:
    """Constructing without sources raises a definition error."""

    with pytest.raises(MacroDefinitionError):
        MacroRepository([])


# === Error & Edge Handling ===
# Export writes deterministic JSON; empty sources raise immediately.


# === Performance Considerations ===
# Temporary files ensure test isolation and avoid repeated catalogue parsing.
