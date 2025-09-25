"""API integration and plugin registry utilities."""

from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, MutableMapping, Optional, Sequence, Tuple

from ..config import settings
from ..plugins import (
    EnergyAdvisorResult,
    EnergyTradeContext,
    PluginRuntime,
    PricingAdjustment,
    PricingContext,
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


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
        self._runtimes: MutableMapping[str, PluginRuntime] = {}

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

    def plugins(self) -> List[Plugin]:
        return list(self._plugins.values())

    def describe(self) -> Dict[str, Dict[str, object]]:
        return {plugin.name: plugin.as_dict() for plugin in self._plugins.values()}

    def clear(self) -> None:
        self._plugins.clear()
        self._runtimes.clear()

    def attach_runtime(self, name: str, runtime: PluginRuntime) -> None:
        self._runtimes[name] = runtime

    def get_runtime(self, name: str) -> PluginRuntime:
        return self._runtimes[name]

    def get_runtime_optional(self, name: str) -> Optional[PluginRuntime]:
        return self._runtimes.get(name)

    def runtimes(self) -> List[PluginRuntime]:
        return list(self._runtimes.values())


registry = PluginRegistry()

DEFAULT_PLUGIN_ROOT = Path(__file__).resolve().parents[3] / settings.plugin_directory
_auto_load_attempted = False


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


def _resolve_entrypoint(entrypoint: str):
    module_path, separator, attribute = entrypoint.partition(":")
    if not separator:
        module_path, dot, attribute = entrypoint.rpartition(".")
        if not dot:
            raise PluginRegistryError(
                f"Invalid entrypoint '{entrypoint}'. Use 'module:callable' syntax."
            )
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive
        raise PluginRegistryError(f"Unable to import module '{module_path}'") from exc
    try:
        target = getattr(module, attribute)
    except AttributeError as exc:  # pragma: no cover - defensive
        raise PluginRegistryError(
            f"Entrypoint '{entrypoint}' does not expose '{attribute}'"
        ) from exc
    if not callable(target):  # pragma: no cover - defensive
        raise PluginRegistryError(f"Entrypoint '{entrypoint}' is not callable")
    return target


def _activate_plugin(plugin: Plugin) -> Optional[str]:
    if not plugin.entrypoint:
        return None
    try:
        callback = _resolve_entrypoint(plugin.entrypoint)
    except PluginRegistryError as exc:
        plugin.enabled = False
        return f"{plugin.name}: {exc}"

    runtime = PluginRuntime(plugin.name)
    try:
        callback(runtime)
    except Exception as exc:  # pragma: no cover - defensive
        plugin.enabled = False
        return f"{plugin.name}: failed to execute entrypoint - {exc}"

    registry.attach_runtime(plugin.name, runtime)
    return None


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
        activation_error = _activate_plugin(plugin)
        if activation_error:
            errors.append(activation_error)
        loaded.append(plugin)
    return loaded, errors


def reload_default_plugins() -> Tuple[List[Plugin], List[str]]:
    """Reload plugins from the configured plugin directory."""

    return load_plugins_from_directory(DEFAULT_PLUGIN_ROOT)


def _ensure_registry_loaded() -> None:
    global _auto_load_attempted
    if registry.plugins():
        return
    if _auto_load_attempted:
        return
    _auto_load_attempted = True
    try:
        loaded, errors = reload_default_plugins()
    except FileNotFoundError:
        logger.warning("Default plugin directory '%s' not found", DEFAULT_PLUGIN_ROOT)
        return
    if not loaded:
        logger.warning("No plugins discovered in '%s'", DEFAULT_PLUGIN_ROOT)
    for error in errors:
        logger.warning("Plugin load issue: %s", error)


def _iter_enabled_plugins() -> Iterable[Plugin]:
    for plugin in registry.plugins():
        if plugin.enabled:
            yield plugin


def collect_pricing_adjustments(
    context: PricingContext,
) -> List[Tuple[str, PricingAdjustment]]:
    """Return pricing adjustments supplied by enabled plugins."""

    _ensure_registry_loaded()
    adjustments: List[Tuple[str, PricingAdjustment]] = []
    for plugin in _iter_enabled_plugins():
        runtime = registry.get_runtime_optional(plugin.name)
        if runtime is None:
            continue
        for adjuster in runtime.pricing_adjusters:
            try:
                result = adjuster(context)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Plugin '%s' adjuster error: %s", plugin.name, exc)
                continue
            if result is None or result.amount == 0:
                continue
            adjustments.append((plugin.name, result))
    return adjustments


def collect_energy_recommendations(
    context: EnergyTradeContext,
) -> List[Tuple[str, EnergyAdvisorResult]]:
    """Return energy optimisation advice from enabled plugins."""

    _ensure_registry_loaded()
    recommendations: List[Tuple[str, EnergyAdvisorResult]] = []
    for plugin in _iter_enabled_plugins():
        runtime = registry.get_runtime_optional(plugin.name)
        if runtime is None:
            continue
        for advisor in runtime.energy_advisors:
            try:
                result = advisor(context)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Plugin '%s' energy advisor error: %s", plugin.name, exc)
                continue
            if result is None:
                continue
            recommendations.append((plugin.name, result))
    return recommendations


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
