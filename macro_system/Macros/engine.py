"""Header & Purpose: macro expansion engine with analytics and auditing."""

from __future__ import annotations

# === Imports / Dependencies ===
import re
from collections import deque
from pathlib import Path
from typing import Deque, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Set, Tuple

from .catalog import load_macros
from .types import (
    Macro,
    MacroAudit,
    MacroCycleError,
    MacroNotFoundError,
    MacroRenderError,
    MacroStats,
    MacroValidationError,
)

# === Types / Interfaces / Schemas ===
# ``MacroEngine`` consumes :class:`Macro` instances and emits audit dataclasses.


_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}")


# === Core Logic / Implementation ===
class MacroEngine:
    """Expand macros, analyse dependency graphs, and surface catalogue insights."""

    def __init__(self, macros: Mapping[str, Macro]):
        self._macros: Dict[str, Macro] = dict(macros)
        self._graph: Dict[str, Tuple[str, ...]] = {
            name: tuple(macro.calls) for name, macro in self._macros.items()
        }
        self._reverse_graph: Dict[str, List[str]] = self._build_reverse_graph()
        self._cache: Dict[str, str] = {}
        self._depth_cache: Dict[str, int] = {}

    @classmethod
    def from_json(cls, path: str | Path) -> "MacroEngine":
        """Instantiate the engine from a JSON file."""

        return cls(load_macros(path))

    # --- Expansion --------------------------------------------------
    def expand(self, macro_name: str, *, use_cache: bool = True) -> str:
        """Return the fully expanded text for ``macro_name``."""

        if macro_name not in self._macros:
            raise MacroNotFoundError(f"Macro '{macro_name}' is not defined.")

        memo = self._cache if use_cache else {}
        return self._expand_recursive(macro_name, [], memo, trace=None)

    def expand_many(self, macro_names: Iterable[str], *, use_cache: bool = True) -> str:
        """Expand multiple macros, reusing memoized expansions where possible."""

        memo = self._cache if use_cache else {}
        sections: List[str] = []
        for name in macro_names:
            if name not in self._macros:
                raise MacroNotFoundError(f"Macro '{name}' is not defined.")
            sections.append(self._expand_recursive(name, [], memo, trace=None))
        return "\n\n".join(sections)

    def expand_with_trace(
        self, macro_name: str, *, use_cache: bool = True
    ) -> Tuple[str, List[str]]:
        """Expand ``macro_name`` and return the expansion with a traversal trace."""

        if macro_name not in self._macros:
            raise MacroNotFoundError(f"Macro '{macro_name}' is not defined.")

        memo = self._cache if use_cache else {}
        trace: List[str] = []
        result = self._expand_recursive(macro_name, [], memo, trace)
        return result, trace

    def clear_cache(self) -> None:
        """Clear memoized expansions."""

        self._cache.clear()

    def cache_info(self) -> Dict[str, int]:
        """Return information about cached macro expansions."""

        return {"cached_macros": len(self._cache)}

    def render(
        self,
        macro_name: str,
        context: Mapping[str, object],
        *,
        use_cache: bool = True,
        strict: bool = True,
    ) -> str:
        """Expand ``macro_name`` and apply ``context`` placeholder substitutions."""

        expansion = self.expand(macro_name, use_cache=use_cache)
        return self.render_text(expansion, context, strict=strict)

    def render_many(
        self,
        macro_names: Iterable[str],
        context: Mapping[str, object],
        *,
        use_cache: bool = True,
        strict: bool = True,
    ) -> str:
        """Render multiple macros with shared placeholder substitutions."""

        sections: List[str] = []
        for name in macro_names:
            sections.append(
                self.render(name, context, use_cache=use_cache, strict=strict)
            )
        return "\n\n".join(sections)

    @staticmethod
    def render_text(
        text: str, context: Mapping[str, object], *, strict: bool = True
    ) -> str:
        """Apply ``context`` substitutions to ``text`` containing ``{{placeholder}}`` tokens."""

        placeholders = {match.group(1).strip() for match in _PLACEHOLDER_PATTERN.finditer(text)}
        missing = sorted(name for name in placeholders if name not in context)
        if missing and strict:
            joined = ", ".join(missing)
            raise MacroRenderError(
                f"Missing values for placeholders: {joined}. Provide context mappings."
            )

        def _replace(match: re.Match[str]) -> str:
            key = match.group(1).strip()
            if key in context:
                value = context[key]
                return str(value)
            return match.group(0)

        return _PLACEHOLDER_PATTERN.sub(_replace, text)

    # --- Discovery --------------------------------------------------
    def available_macros(self) -> List[str]:
        """Return a sorted list of available macro names."""

        return sorted(self._macros)

    def search(
        self,
        query: str,
        *,
        include_expansions: bool = True,
        include_metadata: bool = True,
    ) -> List[Macro]:
        """Search macros by name, expansion text, and optionally metadata values."""

        lowered = query.casefold()
        matches: List[Macro] = []
        for macro in self._macros.values():
            if lowered in macro.name.casefold():
                matches.append(macro)
                continue
            if include_expansions and lowered in macro.expansion.casefold():
                matches.append(macro)
                continue
            if include_metadata:
                metadata_blob = " ".join(str(value) for value in macro.metadata.values())
                if lowered in metadata_blob.casefold():
                    matches.append(macro)
        return sorted(matches, key=lambda item: item.name)

    def placeholders(self, macro_name: str, *, recursive: bool = True) -> List[str]:
        """Return placeholders referenced by ``macro_name`` and optionally its dependencies."""

        if macro_name not in self._macros:
            raise MacroNotFoundError(f"Macro '{macro_name}' is not defined.")

        collected: Set[str] = set()
        visited: Set[str] = set()
        stack: List[str] = []

        def _walk(name: str) -> None:
            if name in stack:
                cycle = stack[stack.index(name) :] + [name]
                raise MacroCycleError(" -> ".join(cycle))
            if name in visited:
                return

            macro = self._macros.get(name)
            if macro is None:
                raise MacroNotFoundError(f"Macro '{name}' is not defined.")

            stack.append(name)
            collected.update(self._extract_placeholders(macro.expansion))
            if recursive:
                for child in macro.calls:
                    if child not in self._macros:
                        raise MacroNotFoundError(
                            f"Macro '{name}' references undefined macro '{child}'."
                        )
                    _walk(child)
            stack.pop()
            visited.add(name)

        _walk(macro_name)
        return sorted(collected)

    def filter_by_metadata(
        self,
        filters: Mapping[str, str],
        *,
        case_sensitive: bool = False,
        match_all: bool = True,
    ) -> List[Macro]:
        """Return macros whose metadata matches ``filters``.

        Parameters
        ----------
        filters:
            Mapping of metadata key/value pairs to match. Keys are matched exactly
            while values use string comparison. When ``filters`` is empty, the
            method returns all macros sorted alphabetically.
        case_sensitive:
            When ``True`` perform case-sensitive comparisons; otherwise the
            comparisons are case-insensitive.
        match_all:
            Require all filters to match (logical AND). When ``False`` the method
            returns macros that satisfy any filter (logical OR).
        """

        if not filters:
            return sorted(self._macros.values(), key=lambda macro: macro.name)

        prepared = {
            key: value if case_sensitive else value.casefold()
            for key, value in filters.items()
        }

        matches: List[Macro] = []
        for macro in self._macros.values():
            metadata = macro.metadata or {}
            if not metadata:
                continue

            comparisons: List[bool] = []
            for key, expected in prepared.items():
                raw_value = metadata.get(key)
                if raw_value is None:
                    comparisons.append(False)
                    continue
                values = (
                    [str(item) for item in raw_value]
                    if isinstance(raw_value, (list, tuple, set))
                    else [str(raw_value)]
                )
                if not case_sensitive:
                    values = [value.casefold() for value in values]
                comparisons.append(expected in values)

            if match_all and all(comparisons):
                matches.append(macro)
            elif not match_all and any(comparisons):
                matches.append(macro)

        return sorted(matches, key=lambda macro: macro.name)

    def group_by_metadata(
        self, key: str, *, case_sensitive: bool = False
    ) -> Dict[str, List[Macro]]:
        """Group macros by the value stored under ``key`` in their metadata."""

        if not key:
            raise ValueError("Metadata key must be a non-empty string.")

        grouped: Dict[str, List[Macro]] = {}
        display_labels: Dict[str, str] = {}

        for macro in self._macros.values():
            metadata = macro.metadata or {}
            raw_value = metadata.get(key)
            if raw_value is None:
                continue

            values = (
                [str(item) for item in raw_value]
                if isinstance(raw_value, (list, tuple, set))
                else [str(raw_value)]
            )

            for value in values:
                normalised = value if case_sensitive else value.casefold()
                display_labels.setdefault(normalised, value)
                grouped.setdefault(normalised, []).append(macro)

        ordered: Dict[str, List[Macro]] = {}
        for normalised in sorted(grouped):
            label = display_labels[normalised]
            ordered[label] = sorted(grouped[normalised], key=lambda macro: macro.name)
        return ordered

    def describe(self, macro_name: str) -> Macro:
        """Return the :class:`Macro` definition for ``macro_name``."""

        try:
            return self._macros[macro_name]
        except KeyError as exc:  # pragma: no cover - simple passthrough
            raise MacroNotFoundError(f"Macro '{macro_name}' is not defined.") from exc

    def dependencies(self, macro_name: str, *, recursive: bool = True) -> List[str]:
        """Return direct or transitive dependencies for ``macro_name``."""

        if macro_name not in self._macros:
            raise MacroNotFoundError(f"Macro '{macro_name}' is not defined.")

        if not recursive:
            return list(self._graph[macro_name])

        ordered: List[str] = []
        seen: Set[str] = set()

        def _walk(name: str) -> None:
            for called in self._graph[name]:
                if called not in self._macros:
                    raise MacroNotFoundError(
                        f"Macro '{macro_name}' references undefined macro '{called}'."
                    )
                if called not in seen:
                    seen.add(called)
                    ordered.append(called)
                    _walk(called)

        _walk(macro_name)
        return ordered

    def ancestors(self, macro_name: str, *, recursive: bool = True) -> List[str]:
        """Return macros that reference ``macro_name`` directly or transitively."""

        if macro_name not in self._macros:
            raise MacroNotFoundError(f"Macro '{macro_name}' is not defined.")

        if not recursive:
            return list(self._reverse_graph.get(macro_name, []))

        ordered: List[str] = []
        seen: Set[str] = set()

        def _walk(name: str) -> None:
            for parent in self._reverse_graph.get(name, []):
                if parent not in seen:
                    seen.add(parent)
                    ordered.append(parent)
                    _walk(parent)

        _walk(macro_name)
        return ordered

    def dependency_graph(self) -> Dict[str, List[str]]:
        """Return a copy of the macro dependency graph."""

        return {name: list(children) for name, children in self._graph.items()}

    def reverse_dependency_graph(self) -> Dict[str, List[str]]:
        """Return the reverse dependency graph mapping macros to parents."""

        return {name: list(parents) for name, parents in self._reverse_graph.items()}

    def stats(self) -> MacroStats:
        """Return structural statistics about the macro catalogue."""

        total = len(self._macros)
        roots = sorted(name for name, parents in self._reverse_graph.items() if not parents)
        leaves = sorted(name for name, macro in self._macros.items() if not macro.calls)
        depths = [self._compute_depth(name) for name in self._macros]
        max_depth = max(depths) if depths else 0
        avg_branching = (
            sum(len(macro.calls) for macro in self._macros.values()) / total if total else 0.0
        )
        return MacroStats(
            total_macros=total,
            root_macros=roots,
            leaf_macros=leaves,
            max_depth=max_depth,
            average_branching_factor=avg_branching,
        )

    # --- Validation & Auditing --------------------------------------
    def validate(self) -> None:
        """Ensure all macros can expand without missing references or cycles."""

        visiting: List[str] = []
        resolved: Dict[str, bool] = {}

        def _dfs(name: str) -> None:
            if name in resolved:
                return
            if name in visiting:
                cycle = visiting[visiting.index(name) :] + [name]
                raise MacroCycleError(" -> ".join(cycle))
            if name not in self._macros:
                raise MacroNotFoundError(f"Macro '{name}' is not defined.")

            visiting.append(name)
            for called in self._graph[name]:
                if called not in self._macros:
                    raise MacroNotFoundError(
                        f"Macro '{name}' references undefined macro '{called}'."
                    )
                _dfs(called)
            visiting.pop()
            resolved[name] = True

        for macro_name in self._macros:
            _dfs(macro_name)

    def validate_strict(self, entrypoints: Iterable[str] | None = None) -> None:
        """Raise :class:`MacroValidationError` if auditing finds any anomalies."""

        audit = self.audit(entrypoints=entrypoints)
        problems: List[str] = []
        if audit.undefined_references:
            details = ", ".join(
                f"{macro}->{missing}" for macro, missing in audit.undefined_references.items()
            )
            problems.append(f"Undefined macro references detected: {details}.")
        if audit.cycles:
            rendered = ", ".join(" -> ".join(path) for path in audit.cycles)
            problems.append(f"Cycles detected: {rendered}.")
        if entrypoints and audit.unreachable_macros:
            problems.append(
                "Unreachable macros from entrypoints: " + ", ".join(audit.unreachable_macros)
            )
        if problems:
            raise MacroValidationError(" ".join(problems))

    def audit(self, entrypoints: Iterable[str] | None = None) -> MacroAudit:
        """Return a catalogue audit without raising, highlighting potential issues."""

        if entrypoints is not None:
            entry_list = list(dict.fromkeys(entrypoints))
            for macro_name in entry_list:
                if macro_name not in self._macros:
                    raise MacroNotFoundError(f"Entry macro '{macro_name}' is not defined.")
        else:
            entry_list = sorted(name for name, parents in self._reverse_graph.items() if not parents)

        undefined: Dict[str, List[str]] = {}
        for name, macro in self._macros.items():
            missing = sorted({child for child in macro.calls if child not in self._macros})
            if missing:
                undefined[name] = missing

        cycles = self._find_cycles()
        reachable = self._reachable(entry_list) if entry_list else set(self._macros)
        unreachable = sorted(set(self._macros) - reachable)

        return MacroAudit(
            undefined_references=undefined,
            cycles=cycles,
            unreachable_macros=unreachable,
            entrypoints=entry_list,
            stats=self.stats(),
        )

    def explain_path(self, source: str, target: str) -> List[str]:
        """Return a dependency path from ``source`` to ``target`` if one exists."""

        if source not in self._macros:
            raise MacroNotFoundError(f"Macro '{source}' is not defined.")
        if target not in self._macros:
            raise MacroNotFoundError(f"Macro '{target}' is not defined.")

        queue: Deque[Tuple[str, List[str]]] = deque([(source, [source])])
        seen: Set[str] = {source}
        while queue:
            node, path = queue.popleft()
            if node == target:
                return path
            for child in self._graph.get(node, ()):  # type: ignore[arg-type]
                if child not in self._macros:
                    continue
                if child not in seen:
                    seen.add(child)
                    queue.append((child, path + [child]))
        return []

    # --- Internal Helpers -------------------------------------------
    def _expand_recursive(
        self,
        name: str,
        stack: List[str],
        memo: MutableMapping[str, str],
        trace: List[str] | None,
    ) -> str:
        if name in memo:
            if trace is not None:
                trace.append(f"{name} (cached)")
            return memo[name]

        if name in stack:
            cycle = stack[stack.index(name) :] + [name]
            raise MacroCycleError(" -> ".join(cycle))

        macro = self._macros.get(name)
        if macro is None:
            raise MacroNotFoundError(f"Macro '{name}' is not defined.")

        stack.append(name)
        if trace is not None:
            trace.append(name)

        sections = [macro.expansion]
        for called in macro.calls:
            sections.append(self._expand_recursive(called, stack, memo, trace))
        stack.pop()

        result = "\n\n".join(sections)
        memo[name] = result
        return result

    @staticmethod
    def _extract_placeholders(text: str) -> Set[str]:
        """Extract placeholder tokens from ``text`` without duplicates."""

        return {
            match.group(1).strip()
            for match in _PLACEHOLDER_PATTERN.finditer(text)
        }

    def _build_reverse_graph(self) -> Dict[str, List[str]]:
        reverse: Dict[str, List[str]] = {name: [] for name in self._macros}
        for parent, macro in self._macros.items():
            for child in macro.calls:
                reverse.setdefault(child, []).append(parent)
        return reverse

    def _compute_depth(self, name: str) -> int:
        if name in self._depth_cache:
            return self._depth_cache[name]

        children = self._graph.get(name, ())
        depth = 1
        if children:
            depth += max(self._compute_depth(child) for child in children if child in self._macros)
        self._depth_cache[name] = depth
        return depth

    def _find_cycles(self) -> List[List[str]]:
        cycles: Set[Tuple[str, ...]] = set()
        visiting: List[str] = []
        visited: Set[str] = set()

        def _dfs(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                cycle = visiting[visiting.index(node) :] + [node]
                cycles.add(self._canonical_cycle(tuple(cycle)))
                return
            visiting.append(node)
            for child in self._graph.get(node, ()):  # type: ignore[arg-type]
                if child in self._macros:
                    _dfs(child)
            visiting.pop()
            visited.add(node)

        for name in self._macros:
            _dfs(name)
        return [list(cycle) for cycle in sorted(cycles)]

    def _canonical_cycle(self, cycle: Tuple[str, ...]) -> Tuple[str, ...]:
        if len(cycle) <= 1:
            return cycle
        base = list(cycle[:-1]) if cycle[0] == cycle[-1] else list(cycle)
        if not base:
            return cycle
        min_index = min(range(len(base)), key=lambda idx: base[idx])
        rotated = base[min_index:] + base[:min_index]
        return tuple(rotated + [rotated[0]])

    def _reachable(self, entrypoints: Sequence[str]) -> Set[str]:
        reachable: Set[str] = set()
        stack: List[str] = list(entrypoints)
        while stack:
            node = stack.pop()
            if node in reachable or node not in self._macros:
                continue
            reachable.add(node)
            for child in self._graph.get(node, ()):  # type: ignore[arg-type]
                stack.append(child)
        return reachable


# === Error & Edge Handling ===
# Dedicated exceptions signal missing macros, cycles, and aggregate validation issues.


# === Performance Considerations ===
# Memoisation caches expansions and depth computations to maintain O(N + E) traversal.


# === Exports / Public API ===
__all__ = ["MacroEngine"]
