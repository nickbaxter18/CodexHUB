"""Recursive macro expansion engine with introspection helpers."""

# === Imports ===
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Sequence

from .macros import load_macros
from .types import Macro, MacroCycleError, MacroNotFoundError

# === Implementation ===


class MacroEngine:
    """Engine that expands macros defined in JSON."""

    def __init__(self, macros: Mapping[str, Macro]):
        self._macros: Dict[str, Macro] = dict(macros)
        self._graph: Dict[str, Sequence[str]] = {
            name: tuple(macro.calls) for name, macro in self._macros.items()
        }
        self._cache: Dict[str, str] = {}
        self._listeners: List[Callable[[str, str], None]] = []

    @classmethod
    def from_json(cls, path: str | Path) -> "MacroEngine":
        """Instantiate the engine from a JSON file."""

        return cls(load_macros(path))

    def expand(self, macro_name: str) -> str:
        """Return the fully expanded text for ``macro_name``."""

        if macro_name not in self._macros:
            raise MacroNotFoundError(f"Macro '{macro_name}' is not defined.")

        result = self._expand_recursive(macro_name, [], self._cache)
        return result

    def expand_many(self, macro_names: Iterable[str]) -> str:
        """Expand multiple macros, reusing memoized expansions where possible."""

        sections: List[str] = []
        for name in macro_names:
            if name not in self._macros:
                raise MacroNotFoundError(f"Macro '{name}' is not defined.")
            sections.append(self._expand_recursive(name, [], self._cache))
        return "\n\n".join(sections)

    def available_macros(self) -> List[str]:
        """Return a sorted list of available macro names."""

        return sorted(self._macros)

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
        seen = set()

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

    def dependency_graph(self) -> Dict[str, Sequence[str]]:
        """Return a copy of the macro dependency graph."""

        return {name: list(children) for name, children in self._graph.items()}

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

    def register_listener(self, callback: Callable[[str, str], None]) -> None:
        """Register a callback invoked whenever a macro is freshly expanded."""

        self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[str, str], None]) -> None:
        """Remove a previously registered expansion callback if present."""

        try:
            self._listeners.remove(callback)
        except ValueError:  # pragma: no cover - defensive guard
            pass

    def invalidate_cache(self) -> None:
        """Clear any memoised expansions."""

        self._cache.clear()

    def cache_size(self) -> int:
        """Return the number of cached macro expansions."""

        return len(self._cache)

    def _expand_recursive(self, name: str, stack: List[str], memo: Dict[str, str]) -> str:
        if name in memo:
            return memo[name]

        if name in stack:
            cycle = stack[stack.index(name) :] + [name]
            raise MacroCycleError(" -> ".join(cycle))

        macro = self._macros.get(name)
        if macro is None:
            raise MacroNotFoundError(f"Macro '{name}' is not defined.")

        stack.append(name)
        sections = [macro.expansion]
        for called in macro.calls:
            sections.append(self._expand_recursive(called, stack, memo))
        stack.pop()

        result = "\n\n".join(sections)
        memo[name] = result
        self._emit_event(name, result)
        return result

    def _emit_event(self, name: str, expansion: str) -> None:
        """Notify registered listeners of a newly calculated expansion."""

        for callback in list(self._listeners):
            callback(name, expansion)


# === Performance ===
# Memoization is implemented within ``_expand_recursive`` to avoid
# re-expanding previously resolved macros.


# === Exports ===
__all__ = ["MacroEngine"]

