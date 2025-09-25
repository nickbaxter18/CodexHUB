"""Utilities for loading and executing news plugins."""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import inspect
import logging
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, List, Sequence

from .news_fetcher import NewsArticle
from .plugins import NewsPlugin, PluginError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PluginSpec:
    """Metadata required to safely reconstruct a plugin in a sandbox."""

    label: str
    module: str
    qualname: str
    module_path: str | None


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise PluginError(f"Unable to load plugin from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


def _annotate_plugin(plugin: NewsPlugin, module: ModuleType) -> NewsPlugin:
    plugin._sandbox_module_file = getattr(module, "__file__", None)  # type: ignore[attr-defined]
    return plugin


def _iter_candidates(module: ModuleType) -> Iterable[NewsPlugin]:
    for attribute in module.__dict__.values():
        if (
            inspect.isclass(attribute)
            and hasattr(attribute, "fetch")
            and hasattr(attribute, "name")
        ):
            instance = attribute()  # type: ignore[call-arg]
            if isinstance(instance, NewsPlugin):
                yield _annotate_plugin(instance, module)
        elif isinstance(attribute, NewsPlugin):
            yield _annotate_plugin(attribute, module)


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


def _build_spec(plugin: NewsPlugin) -> PluginSpec:
    module = plugin.__class__.__module__
    qualname = plugin.__class__.__qualname__
    module_file = getattr(plugin, "_sandbox_module_file", None)
    label = getattr(plugin, "name", plugin.__class__.__name__)
    return PluginSpec(label=label, module=module, qualname=qualname, module_path=module_file)


def _serialise_article(article: Any) -> Dict[str, Any]:
    if isinstance(article, NewsArticle):
        payload = {
            "title": article.title,
            "description": article.description,
            "url": article.url,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "source": article.source,
        }
        return payload
    if hasattr(article, "title") and hasattr(article, "url"):
        payload = {
            "title": getattr(article, "title", ""),
            "description": getattr(article, "description", None),
            "url": getattr(article, "url", ""),
            "published_at": None,
            "source": getattr(article, "source", None),
        }
        published = getattr(article, "published_at", None)
        if isinstance(published, datetime):
            payload["published_at"] = published.isoformat()
        return payload
    if isinstance(article, dict):
        payload = dict(article)
        published = payload.get("published_at")
        if isinstance(published, datetime):
            payload["published_at"] = published.isoformat()
        return payload
    raise PluginError("Plugins must return NewsArticle instances or dictionaries")


def _deserialize_article(payload: Dict[str, Any]) -> NewsArticle:
    published = payload.get("published_at")
    parsed: datetime | None = None
    if isinstance(published, str):
        try:
            parsed = datetime.fromisoformat(published)
        except ValueError:
            parsed = None
    elif isinstance(published, datetime):
        parsed = published
    return NewsArticle(
        title=payload.get("title") or "",
        description=payload.get("description"),
        url=payload.get("url") or "",
        published_at=parsed,
        source=payload.get("source"),
    )


def _execute_in_subprocess(
    spec: PluginSpec,
    config: Dict[str, Any],
    sys_path: List[str],
) -> List[Dict[str, Any]]:
    try:
        sys.path = list(dict.fromkeys(sys_path + sys.path))
        if spec.module_path:
            module_dir = str(Path(spec.module_path).parent)
            if module_dir and module_dir not in sys.path:
                sys.path.insert(0, module_dir)
        module = importlib.import_module(spec.module)
        target: Any = module
        for part in spec.qualname.split("."):
            target = getattr(target, part)
        instance = target()
        result = instance.fetch(config, cache=None, monitor=None)
        if inspect.isawaitable(result):
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                value = loop.run_until_complete(result)
            finally:
                asyncio.set_event_loop(None)
                loop.close()
        else:
            value = result
        return [_serialise_article(item) for item in value]
    except Exception as exc:  # pragma: no cover - executed in subprocess
        raise PluginError(f"{spec.label} execution failed: {exc}") from exc


async def execute_plugins(
    plugins: Iterable[NewsPlugin],
    config: Dict[str, Any],
    *,
    cache: Any | None = None,
    monitor: Any | None = None,
    sandbox: bool = True,
    timeout: float = 30.0,
    max_workers: int | None = None,
) -> List[NewsArticle]:
    """Execute plugins concurrently and collect their results."""

    plugin_list = list(plugins)
    if not plugin_list:
        return []

    specs = [_build_spec(plugin) for plugin in plugin_list]
    settings: List[Dict[str, Any]] = []
    for plugin in plugin_list:
        plugin_cfg: Dict[str, Any] = {}
        if isinstance(config, dict):
            plugin_cfg = config.get(getattr(plugin, "name", ""), {})
        settings.append(plugin_cfg)

    labels = [spec.label for spec in specs]
    articles: List[NewsArticle] = []

    if not sandbox:
        tasks: List[asyncio.Task] = []
        for plugin, plugin_cfg, _label in zip(plugin_list, settings, labels, strict=False):
            result = plugin.fetch(plugin_cfg, cache=cache, monitor=monitor)
            if inspect.isawaitable(result):
                task = asyncio.create_task(result)
            else:

                async def _wrap(value: Iterable[NewsArticle]) -> List[NewsArticle]:
                    return list(value)

                task = asyncio.create_task(_wrap(result))
            tasks.append(task)

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

    sys_path = list(sys.path)
    worker_count = max_workers or min(len(specs), os.cpu_count() or 1) or 1
    loop = asyncio.get_running_loop()

    async def _submit(
        executor: ProcessPoolExecutor,
        spec: PluginSpec,
        plugin_cfg: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        future = loop.run_in_executor(
            executor,
            _execute_in_subprocess,
            spec,
            plugin_cfg,
            sys_path,
        )
        return await asyncio.wait_for(future, timeout)

    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        tasks = [
            asyncio.create_task(_submit(executor, spec, cfg))
            for spec, cfg in zip(specs, settings, strict=False)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for label, result in zip(labels, results, strict=False):
        if isinstance(result, asyncio.TimeoutError):
            logger.warning("Plugin %s timed out after %.1fs", label, timeout)
            error = PluginError(f"{label} timed out after {timeout} seconds")
            if monitor is not None and hasattr(monitor, "record_error"):
                monitor.record_error(label, error)
            continue
        if isinstance(result, Exception):
            logger.exception("Plugin %s failed", label, exc_info=result)
            if monitor is not None and hasattr(monitor, "record_error"):
                monitor.record_error(label, result)
            continue
        try:
            deserialised = [_deserialize_article(item) for item in result]
        except Exception as exc:  # pragma: no cover - defensive conversion
            logger.exception("Failed to deserialize results from %s", label, exc_info=exc)
            if monitor is not None and hasattr(monitor, "record_error"):
                monitor.record_error(label, exc)
            continue
        if monitor is not None and hasattr(monitor, "record_articles"):
            monitor.record_articles(label, len(deserialised))
        articles.extend(deserialised)

    return articles


__all__ = ["discover_plugins", "execute_plugins", "PluginSpec"]
