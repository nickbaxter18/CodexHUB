"""Runtime plugin loader for the Stage 3 runner."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Optional

from ..config import get_config
from ..plugins import PluginRegistry
from ..types import PluginMetadata
from .logger import get_logger

LOGGER = get_logger("plugin_loader")


class PluginLoader:
    """Discover and load runtime plugins from a directory."""

    def __init__(
        self,
        plugin_directory: Optional[Path] = None,
        registry: Optional[PluginRegistry] = None,
    ) -> None:
        config = get_config()
        self.plugin_directory = plugin_directory or config.plugin_directory
        self.plugin_directory.mkdir(parents=True, exist_ok=True)
        self.registry = registry or PluginRegistry()
        self._metadata: Dict[str, PluginMetadata] = {}

    def discover(self) -> List[Path]:
        """Return plugin module paths available on disk."""

        if not self.plugin_directory.exists():
            return []
        return sorted(
            path
            for path in self.plugin_directory.glob("*.py")
            if path.name not in {"__init__.py", "__pycache__"}
        )

    def load_plugins(self) -> List[PluginMetadata]:
        """Load all plugins from the configured directory."""

        self.registry.reset()
        self._metadata.clear()
        loaded: List[PluginMetadata] = []
        for module_path in self.discover():
            metadata = self._import_plugin(module_path)
            if metadata is None:
                continue
            self._metadata[metadata.name] = metadata
            loaded.append(metadata)
        return loaded

    def reload(self) -> List[PluginMetadata]:
        """Reload all plugins and return their metadata."""

        return self.load_plugins()

    def list_plugins(self) -> List[PluginMetadata]:
        return list(self._metadata.values())

    def set_enabled(self, name: str, enabled: bool) -> PluginMetadata:
        metadata = self._metadata.get(name)
        if metadata is None:
            raise KeyError(f"Unknown plugin: {name}")
        metadata.enabled = enabled
        return metadata

    def registry_snapshot(self) -> Dict[str, object]:
        return self.registry.snapshot()

    def _import_plugin(self, module_path: Path) -> Optional[PluginMetadata]:
        module_name = f"runner_plugin_{module_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            LOGGER.warning("Skipping plugin %s: unable to create module spec", module_path)
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:  # noqa: BLE001
            LOGGER.exception("Failed to import plugin module %s", module_path)
            return None
        metadata = self._register_module(module, module_path)
        if metadata:
            LOGGER.info("Loaded plugin %s", metadata.name)
        return metadata

    def _register_module(self, module: ModuleType, module_path: Path) -> Optional[PluginMetadata]:
        if not hasattr(module, "register"):
            return PluginMetadata(
                name=module_path.stem,
                description="Auto-discovered plugin",
                enabled=True,
                entrypoint=module.__name__,
            )
        register = getattr(module, "register")
        if not callable(register):
            LOGGER.warning("Plugin %s has non-callable register attribute", module.__name__)
            return None
        try:
            result = register(self.registry)
        except Exception:  # noqa: BLE001
            LOGGER.exception("Plugin %s failed during registration", module.__name__)
            return None
        metadata = self._coerce_metadata(result, module, module_path)
        return metadata

    def _coerce_metadata(
        self, result: object, module: ModuleType, module_path: Path
    ) -> PluginMetadata:
        if isinstance(result, PluginMetadata):
            metadata = result
        elif isinstance(result, dict):
            metadata = PluginMetadata(
                name=str(result.get("name", module_path.stem)),
                description=str(result.get("description", "")),
                version=str(result.get("version", "0.0.0")),
                enabled=bool(result.get("enabled", True)),
                entrypoint=module.__name__,
            )
        else:
            metadata = PluginMetadata(
                name=module_path.stem,
                description="Runtime plugin",
                enabled=True,
                entrypoint=module.__name__,
            )
        if not metadata.name:
            metadata.name = module_path.stem
        return metadata


DEFAULT_PLUGIN_LOADER = PluginLoader()
