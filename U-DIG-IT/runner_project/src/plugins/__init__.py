"""Plugin support primitives used by the Stage 3 runner."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Protocol


class PluginRegistry:
    """Simple registry exposing extension points to plugins."""

    def __init__(self) -> None:
        self.commands: Dict[str, Callable[..., Any]] = {}
        self.hooks: Dict[str, List[Callable[..., Any]]] = {}

    def register_command(self, name: str, handler: Callable[..., Any]) -> None:
        self.commands[name] = handler

    def register_hook(self, name: str, handler: Callable[..., Any]) -> None:
        self.hooks.setdefault(name, []).append(handler)

    def reset(self) -> None:
        self.commands.clear()
        self.hooks.clear()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "commands": list(self.commands.keys()),
            "hooks": {key: len(value) for key, value in self.hooks.items()},
        }


class PluginModule(Protocol):
    """Protocol describing the expected plugin interface."""

    def register(self, registry: PluginRegistry) -> Dict[str, Any]: ...
