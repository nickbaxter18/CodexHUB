"""Utilities for loading and executing news plugins."""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import inspect
import logging
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, List, Sequence

from .news_fetcher import NewsArticle
from .plugins import NewsPlugin, PluginError

logger = logging.getLogger(__name__)


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise PluginError(f"Unable to load plugin from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


def _iter_candidates(module: ModuleType) -> Iterable[NewsPlugin]:
    for attribute in module.__dict__.values():
        if inspect.isclass(attribute) and issubclass(attribute, object):
            if hasattr(attribute, "fetch") and hasattr(attribute, "name"):
                instance = attribute()  # type: ignore[call-arg]
                if isinstance(instance, NewsPlugin):
                    yield instance
        elif isinstance(attribute, NewsPlugin):
            yield attribute


def discover_plugins(
    *,
    packages: Sequence[str] | None = None,
    paths: Sequence[Path] | None = None,
) -> List[NewsPlugin]:
    """Discover plugin instances from *packages* and file *paths*."""

    plugins: List[NewsPlugin] = []

    for module_name in packages or []:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            logger.warning(
                "Failed to import plugin package %s: %s",
                module_name,
                exc,
            )
            continue
        plugins.extend(_iter_candidates(module))

    for file_path in paths or []:
        try:
            module = _load_module(file_path)
        except PluginError as exc:
            logger.warning(
                "Failed to load plugin from %s: %s",
                file_path,
                exc,
            )
            continue
        plugins.extend(_iter_candidates(module))

    unique: Dict[str, NewsPlugin] = {}
    for plugin in plugins:
        unique[getattr(plugin, "name", plugin.__class__.__name__)] = plugin
    return list(unique.values())


async def execute_plugins(
    plugins: Iterable[NewsPlugin],
    config: Dict[str, Any],
    *,
    cache: Any | None = None,
    monitor: Any | None = None,
) -> List[NewsArticle]:
    """Execute plugins concurrently and collect their results."""

    tasks: List[asyncio.Task] = []
    labels: List[str] = []
    for plugin in plugins:
        plugin_cfg: Dict[str, Any] = {}
        if isinstance(config, dict):
            plugin_cfg = config.get(plugin.name, {})
        result = plugin.fetch(plugin_cfg, cache=cache, monitor=monitor)
        if inspect.isawaitable(result):
            task = asyncio.create_task(result)
        else:

            async def _wrap(value: Iterable[NewsArticle]) -> List[NewsArticle]:
                return list(value)

            task = asyncio.create_task(_wrap(result))
        tasks.append(task)
        labels.append(getattr(plugin, "name", plugin.__class__.__name__))

    articles: List[NewsArticle] = []
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for label, result in zip(labels, results, strict=False):
        if isinstance(result, Exception):
            logger.exception("Plugin %s failed", label, exc_info=result)
            if monitor is not None and hasattr(monitor, "record_error"):
                monitor.record_error(label, result)
            continue
        data = list(result)
        if monitor is not None and hasattr(monitor, "record_articles"):
            monitor.record_articles(label, len(data))
        articles.extend(data)
    return articles


__all__ = ["discover_plugins", "execute_plugins"]
