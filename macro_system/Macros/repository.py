"""Header & Purpose: macro catalogue repository with merge and export utilities."""

from __future__ import annotations

# === Imports / Dependencies ===
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from .catalog import CatalogSource, load_catalogs
from .engine import MacroEngine
from .types import Macro, MacroDefinitionError


# === Types / Interfaces / Schemas ===


@dataclass(frozen=True)
class CatalogDescriptor:
    """Lightweight description of a macro catalogue source."""

    label: str
    source: CatalogSource


# === Core Logic / Implementation ===
class MacroRepository:
    """Manage macro catalogues, provide merged views, and export snapshots."""

    def __init__(
        self,
        sources: Sequence[CatalogSource],
    ) -> None:
        if not sources:
            raise MacroDefinitionError(
                "MacroRepository requires at least one catalogue source."
            )
        self._descriptors: List[CatalogDescriptor] = [
            CatalogDescriptor(label=self._describe_source(raw), source=raw)
            for raw in self._deduplicate_sources(sources)
        ]
        self._macros: dict[str, Macro] = {}
        self.refresh()

    # --- Repository Maintenance ------------------------------------
    def refresh(self) -> dict[str, Macro]:
        """Reload catalogue data from all registered sources."""

        merged = load_catalogs([descriptor.source for descriptor in self._descriptors])
        self._macros = merged
        return dict(self._macros)

    def add_source(self, source: CatalogSource) -> dict[str, Macro]:
        """Register an additional catalogue source and refresh immediately."""

        descriptor = CatalogDescriptor(
            label=self._describe_source(source),
            source=source,
        )
        self._descriptors.append(descriptor)
        return self.refresh()

    def sources(self) -> List[str]:
        """Return human-readable descriptions of catalogue sources."""

        return [descriptor.label for descriptor in self._descriptors]

    def macros(self) -> dict[str, Macro]:
        """Return a copy of the merged macros mapping."""

        return dict(self._macros)

    def engine(self) -> MacroEngine:
        """Instantiate a :class:`MacroEngine` backed by the merged macros."""

        return MacroEngine(self._macros)

    def export(self, destination: Path, *, indent: int = 2) -> None:
        """Write the merged catalogue to ``destination`` in deterministic order."""

        payload = {
            name: macro.describe() for name, macro in sorted(self._macros.items())
        }
        destination.write_text(json.dumps(payload, indent=indent), encoding="utf-8")

    def __len__(self) -> int:  # pragma: no cover - trivial proxy
        return len(self._macros)

    # --- Internal Helpers ------------------------------------------
    @staticmethod
    def _describe_source(source: CatalogSource) -> str:
        if isinstance(source, Path):
            return str(source)
        if isinstance(source, str):
            return str(Path(source))
        return "<in-memory-catalog>"

    @staticmethod
    def _deduplicate_sources(sources: Iterable[CatalogSource]) -> List[CatalogSource]:
        seen: dict[str, CatalogSource] = {}
        for source in sources:
            if isinstance(source, (Path, str)):
                key = str(source)
            else:
                key = repr(source)
            seen[key] = source
        return list(seen.values())


# === Error & Edge Handling ===
# ``load_catalogs`` raises :class:`MacroDefinitionError` for invalid catalogue data.


# === Performance Considerations ===
# Repository operations reuse ``load_catalogs`` which performs linear merges across
# catalogue sources; deduplication avoids reprocessing duplicate paths.


# === Exports / Public API ===
__all__ = ["CatalogDescriptor", "MacroRepository"]

