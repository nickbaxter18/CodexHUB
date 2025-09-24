"""API integration and plugin registry utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, MutableMapping, Optional


@dataclass
class Plugin:
    """Represents a dynamically loadable plugin."""

    name: str
    version: str
    description: str = ""
    enabled: bool = True
    permissions: List[str] = field(default_factory=list)
    webhooks: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "enabled": self.enabled,
            "permissions": list(self.permissions),
            "webhooks": list(self.webhooks),
        }


class PluginRegistry:
    """In-memory registry that mimics a plugin marketplace."""

    def __init__(self) -> None:
        self._plugins: MutableMapping[str, Plugin] = {}

    def register(self, plugin: Plugin) -> Plugin:
        self._plugins[plugin.name] = plugin
        return plugin

    def enable(self, name: str) -> None:
        plugin = self._plugins[name]
        plugin.enabled = True

    def disable(self, name: str) -> None:
        plugin = self._plugins[name]
        plugin.enabled = False

    def get(self, name: str) -> Plugin:
        return self._plugins[name]

    def list(self) -> List[Plugin]:
        return list(self._plugins.values())

    def describe(self) -> Dict[str, Dict[str, object]]:
        return {plugin.name: plugin.as_dict() for plugin in self._plugins.values()}


registry = PluginRegistry()


def register_plugin(
    name: str,
    version: str,
    *,
    description: str = "",
    permissions: Optional[Iterable[str]] = None,
    webhooks: Optional[Iterable[str]] = None,
    enabled: bool = True,
) -> Plugin:
    """Register a plugin with metadata.

    The registry allows test doubles to emulate a richer Stage 2 plugin
    marketplace while keeping the implementation deterministic.
    """

    plugin = Plugin(
        name=name,
        version=version,
        description=description,
        permissions=list(permissions or []),
        webhooks=list(webhooks or []),
        enabled=enabled,
    )
    return registry.register(plugin)


def list_plugins() -> Dict[str, Dict[str, object]]:
    """Return all registered plugins."""

    return registry.describe()
