"""Macro dependency compatibility management and blocking orchestration."""

# === Imports / Dependencies ===
from __future__ import annotations

import contextlib
import json
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set


# === Types, Interfaces, Contracts, Schema ===
@dataclass
class MacroState:
    """Snapshot of a macro's schema, dependencies, and block status."""

    macro: str
    schema_version: Optional[str]
    dependencies: Dict[str, str] = field(default_factory=dict)
    blocked: bool = False
    reason: Optional[str] = None
    diff: Dict[str, Any] = field(default_factory=dict)


class MacroDependencyManager:
    """Track macro dependency compatibility and emit block/unblock states."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self._macros: Dict[str, MacroState] = {}
        self._dependency_versions: Dict[str, str] = {}
        self._reverse_index: Dict[str, Set[str]] = {}
        self._lock = threading.RLock()
        self._storage_path = storage_path
        if self._storage_path is not None:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._load()

    # === Core Logic / Implementation ===
    def register_macro(
        self,
        macro: str,
        schema_version: Optional[str],
        dependencies: Mapping[str, str],
    ) -> MacroState:
        """Register or update ``macro`` requirements and return its state."""

        if not macro:
            raise ValueError("macro name must be provided")
        normalized_dependencies = {str(dep): str(version) for dep, version in dependencies.items()}
        normalized_schema = str(schema_version) if schema_version is not None else None
        with self._lock:
            previous = self._macros.get(macro)
            if previous:
                self._remove_reverse_links(macro, previous.dependencies.keys())
            state = MacroState(
                macro=macro, schema_version=normalized_schema, dependencies=normalized_dependencies
            )
            self._macros[macro] = state
            self._add_reverse_links(macro, normalized_dependencies.keys())
            self._evaluate_macro(macro)
            decorated = self._decorate_state(macro, previous)
            self._persist()
            return decorated

    def update_dependency_schema(self, dependency: str, schema_version: str) -> List[MacroState]:
        """Update actual ``dependency`` schema version and return impacted macro states."""

        if not dependency:
            raise ValueError("dependency must be provided")
        normalized = str(schema_version)
        impacted: List[MacroState] = []
        with self._lock:
            self._dependency_versions[dependency] = normalized
            for macro in self._reverse_index.get(dependency, set()):
                previous = self._macros.get(macro)
                if previous is None:
                    continue
                previous_copy = MacroState(
                    macro=previous.macro,
                    schema_version=previous.schema_version,
                    dependencies=dict(previous.dependencies),
                    blocked=previous.blocked,
                    reason=previous.reason,
                )
                if self._evaluate_macro(macro):
                    impacted.append(self._decorate_state(macro, previous_copy))
            if impacted:
                self._persist()
        return impacted

    def get_state(self, macro: str) -> MacroState:
        """Return a defensive copy of the stored state for ``macro``."""

        with self._lock:
            state = self._macros.get(macro)
            if not state:
                raise KeyError(f"macro '{macro}' is not registered")
            return MacroState(
                macro=state.macro,
                schema_version=state.schema_version,
                dependencies=dict(state.dependencies),
                blocked=state.blocked,
                reason=state.reason,
                diff=dict(state.diff),
            )

    def is_blocked(self, macro: str) -> bool:
        """Return True if ``macro`` is currently blocked."""

        return self.get_state(macro).blocked

    def get_block_reason(self, macro: str) -> Optional[str]:
        """Return the block reason for ``macro`` if blocked."""

        return self.get_state(macro).reason

    def get_blocked_macros(self) -> Dict[str, str]:
        """Return mapping of blocked macros to their reasons."""

        with self._lock:
            blocked: Dict[str, str] = {}
            for macro, state in self._macros.items():
                if state.blocked:
                    blocked[macro] = state.reason or ""
            return blocked

    # === Error & Edge Case Handling ===
    def _evaluate_macro(self, macro: str) -> bool:
        state = self._macros[macro]
        previous_blocked = state.blocked
        previous_reason = state.reason
        reason: Optional[str] = None
        for dependency, expected in state.dependencies.items():
            actual = self._dependency_versions.get(dependency)
            if actual is None:
                reason = f"dependency {dependency} schema unknown"
                break
            if actual != expected:
                reason = (
                    f"dependency {dependency} schema mismatch: expected {expected}, got {actual}"
                )
                break
        state.blocked = reason is not None
        state.reason = reason
        return state.blocked != previous_blocked or state.reason != previous_reason

    def _remove_reverse_links(self, macro: str, dependencies: Iterable[str]) -> None:
        for dependency in dependencies:
            watchers = self._reverse_index.get(dependency)
            if not watchers:
                continue
            watchers.discard(macro)
            if not watchers:
                self._reverse_index.pop(dependency, None)

    def _add_reverse_links(self, macro: str, dependencies: Iterable[str]) -> None:
        for dependency in dependencies:
            self._reverse_index.setdefault(dependency, set()).add(macro)

    def _decorate_state(self, macro: str, previous: Optional[MacroState]) -> MacroState:
        current = self._macros[macro]
        diff: Dict[str, object] = {}
        if previous is not None:
            dependency_diff = self._diff_dependencies(previous.dependencies, current.dependencies)
            if any(dependency_diff.values()):
                diff["dependencies"] = dependency_diff
            if previous.schema_version != current.schema_version:
                diff["schema_version"] = {
                    "before": previous.schema_version,
                    "after": current.schema_version,
                }
            if previous.blocked != current.blocked:
                diff["blocked"] = {
                    "before": previous.blocked,
                    "after": current.blocked,
                }
            if previous.reason != current.reason:
                diff["reason"] = {
                    "before": previous.reason,
                    "after": current.reason,
                }
        else:
            diff["initialized_at"] = datetime.now(timezone.utc).isoformat()
        decorated = MacroState(
            macro=current.macro,
            schema_version=current.schema_version,
            dependencies=dict(current.dependencies),
            blocked=current.blocked,
            reason=current.reason,
            diff=diff,
        )
        self._macros[macro] = MacroState(
            macro=current.macro,
            schema_version=current.schema_version,
            dependencies=dict(current.dependencies),
            blocked=current.blocked,
            reason=current.reason,
            diff=diff,
        )
        return decorated

    def _diff_dependencies(
        self, previous: Mapping[str, str], current: Mapping[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        prev_keys = set(previous)
        curr_keys = set(current)
        added: Dict[str, Any] = {key: current[key] for key in curr_keys - prev_keys}
        removed: Dict[str, Any] = {key: previous[key] for key in prev_keys - curr_keys}
        changed: Dict[str, Dict[str, Any]] = {
            key: {"before": previous[key], "after": current[key]}
            for key in prev_keys & curr_keys
            if previous[key] != current[key]
        }
        return {"added": added, "removed": removed, "changed": changed}

    def _persist(self) -> None:
        if self._storage_path is None:
            return
        payload = {
            "macros": {
                macro: {
                    "schema_version": state.schema_version,
                    "dependencies": state.dependencies,
                    "blocked": state.blocked,
                    "reason": state.reason,
                }
                for macro, state in self._macros.items()
            },
            "dependencies": dict(self._dependency_versions),
        }
        serialized = json.dumps(payload, sort_keys=True)
        temp_path = self._storage_path.with_suffix(f"{self._storage_path.suffix}.tmp")
        try:
            temp_path.write_text(serialized, encoding="utf-8")
            os.replace(temp_path, self._storage_path)
        except OSError:
            with contextlib.suppress(FileNotFoundError, OSError):
                temp_path.unlink()

    def _load(self) -> None:
        try:
            raw = self._storage_path.read_text(encoding="utf-8") if self._storage_path else ""
        except (FileNotFoundError, OSError):
            return
        try:
            payload = json.loads(raw)
        except (ValueError, TypeError):
            return
        if not isinstance(payload, dict):
            return
        macros = payload.get("macros", {})
        dependencies = payload.get("dependencies", {})
        if isinstance(macros, dict):
            for macro, state in macros.items():
                if not isinstance(state, dict):
                    continue
                deps = state.get("dependencies", {})
                if isinstance(deps, dict):
                    dependencies_map = {str(dep): str(version) for dep, version in deps.items()}
                else:
                    dependencies_map = {}
                schema_version = state.get("schema_version")
                blocked = bool(state.get("blocked", False))
                reason = state.get("reason")
                macro_state = MacroState(
                    macro=str(macro),
                    schema_version=str(schema_version) if schema_version is not None else None,
                    dependencies=dependencies_map,
                    blocked=blocked,
                    reason=str(reason) if isinstance(reason, str) else None,
                )
                self._macros[str(macro)] = macro_state
                self._add_reverse_links(str(macro), dependencies_map.keys())
        if isinstance(dependencies, dict):
            for dependency, version in dependencies.items():
                self._dependency_versions[str(dependency)] = str(version)


# === Performance / Resource Considerations ===
# Compatibility checks are O(number of dependencies per macro). Reverse indexes ensure only impacted macros
# are evaluated on dependency changes. State copies safeguard callers from accidental mutation.


# === Exports / Public API ===
__all__ = ["MacroDependencyManager", "MacroState"]
