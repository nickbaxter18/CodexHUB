"""API integration and plugin registry utilities."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, MutableMapping, Optional, Sequence, Tuple

from ..config import settings


class PluginRegistryError(RuntimeError):
    """Base error for plugin registry issues."""


class PluginSignatureError(PluginRegistryError):
    """Raised when a plugin manifest signature is invalid."""


@dataclass
class Plugin:
    """Represents a dynamically loadable plugin."""

    name: str
    version: str
    description: str = ""
    enabled: bool = True
    permissions: List[str] = field(default_factory=list)
    webhooks: List[str] = field(default_factory=list)
    entrypoint: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    signature: Optional[str] = None
    source: Optional[str] = None

    def as_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "enabled": self.enabled,
            "permissions": list(self.permissions),
            "webhooks": list(self.webhooks),
            "entrypoint": self.entrypoint,
            "categories": list(self.categories),
            "signature": self.signature,
            "source": self.source,
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

    def clear(self) -> None:
        self._plugins.clear()


registry = PluginRegistry()

DEFAULT_PLUGIN_ROOT = Path(__file__).resolve().parents[3] / settings.plugin_directory


def _normalize_str_iterable(values: object) -> List[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    if isinstance(values, Iterable):
        return [str(item) for item in values]
    raise PluginRegistryError("Expected a sequence of strings")


def _sorted_sequence(values: object) -> List[str]:
    return sorted(_normalize_str_iterable(values))


def _fingerprint_manifest(
    name: str, version: str, permissions: Sequence[str], webhooks: Sequence[str]
) -> str:
    payload = json.dumps(
        {
            "name": name,
            "version": version,
            "permissions": list(permissions),
            "webhooks": list(webhooks),
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _build_plugin_from_manifest(
    manifest: Dict[str, object], *, source: Path, signature_required: bool
) -> Plugin:
    try:
        name = str(manifest["name"])
        version = str(manifest["version"])
    except KeyError as exc:  # pragma: no cover - defensive
        raise PluginRegistryError(f"Manifest missing required field: {exc}") from exc

    permissions = _sorted_sequence(manifest.get("permissions"))
    webhooks = _sorted_sequence(manifest.get("webhooks"))
    signature = manifest.get("signature")
    expected_signature = _fingerprint_manifest(name, version, permissions, webhooks)

    if signature_required and signature != expected_signature:
        raise PluginSignatureError(
            f"Signature mismatch for plugin '{name}'. Expected {expected_signature}"
        )

    plugin = Plugin(
        name=name,
        version=version,
        description=str(manifest.get("description", "")),
        permissions=list(permissions),
        webhooks=list(webhooks),
        entrypoint=str(manifest.get("entrypoint")) if manifest.get("entrypoint") else None,
        categories=_normalize_str_iterable(manifest.get("categories")),
        enabled=bool(manifest.get("enabled", True)),
        signature=str(signature) if signature else None,
        source=str(source),
    )
    return plugin


def register_plugin(
    name: str,
    version: str,
    *,
    description: str = "",
    permissions: Optional[Iterable[str]] = None,
    webhooks: Optional[Iterable[str]] = None,
    enabled: bool = True,
    entrypoint: Optional[str] = None,
    categories: Optional[Iterable[str]] = None,
    signature: Optional[str] = None,
    source: Optional[str] = None,
) -> Plugin:
    """Register a plugin with metadata."""

    plugin = Plugin(
        name=name,
        version=version,
        description=description,
        permissions=list(permissions or []),
        webhooks=list(webhooks or []),
        enabled=enabled,
        entrypoint=entrypoint,
        categories=list(categories or []),
        signature=signature,
        source=source,
    )
    return registry.register(plugin)


def list_plugins() -> Dict[str, Dict[str, object]]:
    """Return all registered plugins."""

    return registry.describe()


def load_plugins_from_directory(
    path: Path, *, strict: Optional[bool] = None
) -> Tuple[List[Plugin], List[str]]:
    """Load plugins from manifest files in *path*.

    Returns a tuple of successfully loaded plugins and any error messages encountered.
    """

    enforce_signature = settings.plugin_signature_enforcement if strict is None else bool(strict)

    if not path.exists():
        raise FileNotFoundError(path)

    registry.clear()
    loaded: List[Plugin] = []
    errors: List[str] = []
    for manifest_path in sorted(path.rglob("plugin.json")):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            plugin = _build_plugin_from_manifest(
                manifest, source=manifest_path, signature_required=enforce_signature
            )
        except (PluginRegistryError, json.JSONDecodeError) as exc:
            errors.append(f"{manifest_path.name}: {exc}")
            continue
        register_plugin(
            plugin.name,
            plugin.version,
            description=plugin.description,
            permissions=plugin.permissions,
            webhooks=plugin.webhooks,
            enabled=plugin.enabled,
            entrypoint=plugin.entrypoint,
            categories=plugin.categories,
            signature=plugin.signature,
            source=plugin.source,
        )
        loaded.append(plugin)
    return loaded, errors


def reload_default_plugins() -> Tuple[List[Plugin], List[str]]:
    """Reload plugins from the configured plugin directory."""

    return load_plugins_from_directory(DEFAULT_PLUGIN_ROOT)


def enable_plugin(name: str) -> Dict[str, object]:
    """Enable a plugin by name and return its metadata."""

    registry.enable(name)
    return registry.get(name).as_dict()


def disable_plugin(name: str) -> Dict[str, object]:
    """Disable a plugin by name and return its metadata."""

    registry.disable(name)
    return registry.get(name).as_dict()


def get_plugin(name: str) -> Dict[str, object]:
    """Return metadata for a single plugin."""

    return registry.get(name).as_dict()
