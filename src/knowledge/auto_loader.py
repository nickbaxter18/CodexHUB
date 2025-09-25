"""
Knowledge Auto-Loader
Automatically loads NDJSON data into Knowledge Agent and keeps it synchronized.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    from watchfiles import DefaultFilter, awatch
except ImportError:  # pragma: no cover - optional dependency fallback
    DefaultFilter = None  # type: ignore[assignment]
    awatch = None  # type: ignore[assignment]

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.specialist_agents import KnowledgeAgent  # noqa: E402
from qa.qa_engine import QAEngine, QARules  # noqa: E402
from qa.qa_event_bus import QAEventBus  # noqa: E402

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())


@dataclass
class KnowledgeSource:
    """Configuration for a knowledge source."""

    name: str
    path: Path
    enabled: bool = True
    last_loaded: Optional[datetime] = None
    document_count: int = 0
    auto_reload: bool = True
    priority: int = 1


if DefaultFilter is not None:

    class _KnowledgeWatchFilter(DefaultFilter):
        """Filter watch events to NDJSON files, respecting ignored directories."""

        def __init__(self, ignored_dirs: set[str]):
            super().__init__(ignore_dirs=tuple(ignored_dirs))

        def __call__(self, change: tuple[int, str]) -> bool:  # type: ignore[override]
            if not super().__call__(change):
                return False

            _, raw_path = change
            return raw_path.endswith(".ndjson")

else:  # pragma: no cover - executed only when watchfiles missing

    class _KnowledgeWatchFilter:  # type: ignore[too-many-ancestors]
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            """Placeholder filter when watchfiles is unavailable."""

            raise RuntimeError("watchfiles is required for knowledge watching")


class KnowledgeAutoLoader:
    """Automatically loads and manages knowledge sources for the Knowledge Agent."""

    def __init__(self, knowledge_agent: KnowledgeAgent):
        self.knowledge_agent = knowledge_agent
        self.sources: List[KnowledgeSource] = []
        self.is_running = False
        self.watch_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self._watch_task: Optional[asyncio.Task[None]] = None
        self.watch_interval = self._resolve_watch_interval()
        self.ignored_directories = {
            ".git",
            "node_modules",
            "__pycache__",
            "cache",
        }

        # Setup default sources
        self._setup_default_sources()

    def _setup_default_sources(self) -> None:
        """Setup default knowledge sources."""

        configured_paths = os.getenv("KNOWLEDGE_NDJSON_PATHS")
        sources: List[KnowledgeSource] = []

        if configured_paths:
            for index, raw_path in enumerate(configured_paths.split(",")):
                candidate = raw_path.strip()
                if not candidate:
                    continue
                path_obj = Path(candidate)
                sources.append(
                    KnowledgeSource(
                        name=f"configured_{index}",
                        path=path_obj,
                        priority=index + 1,
                    )
                )

        if not sources:
            default_sources = [
                KnowledgeSource(
                    name="brain_docs", path=Path("Brain docs cleansed .ndjson"), priority=1
                ),
                KnowledgeSource(
                    name="bundle_docs", path=Path("Bundle cleansed .ndjson"), priority=2
                ),
                KnowledgeSource(
                    name="repository_docs",
                    path=Path("data/knowledge"),
                    priority=3,
                    auto_reload=False,
                ),
            ]
            sources.extend(default_sources)
            logger.info(f"Setup {len(default_sources)} default knowledge sources")

        self.sources.extend(sources)

    async def start_auto_loading(self) -> None:
        """Start automatic knowledge loading."""

        if self.is_running:
            logger.info("Knowledge auto-loader already running")
            return

        self.is_running = True
        logger.info("Starting knowledge auto-loading")

        # Initial load of all sources
        await self._load_all_sources()

        # Start watching for changes without blocking startup
        loop = asyncio.get_running_loop()
        if self.watch_interval:
            self._watch_task = loop.create_task(
                self._watch_for_changes(),
                name="knowledge-auto-loader-watch",
            )
        else:
            logger.info("Knowledge auto-loader started without change watcher (interval disabled)")

    async def _load_all_sources(self) -> None:
        """Load all enabled knowledge sources."""

        for source in self.sources:
            if source.enabled:
                await self._load_source(source)

    async def _load_source(self, source: KnowledgeSource) -> None:
        """Load a specific knowledge source."""

        try:
            if not source.path.exists():
                logger.debug(f"Skipping missing knowledge source: {source.path}")
                return
            if source.path.is_file() and source.path.suffix == ".ndjson":
                # Load single NDJSON file
                loaded_count = self.knowledge_agent.load_ndjson(source.path)
                source.document_count = loaded_count
                source.last_loaded = datetime.now()
                logger.info(f"Loaded {loaded_count} documents from {source.name}")

            elif source.path.is_dir():
                # Load all NDJSON files in directory
                total_loaded = 0
                for ndjson_file in source.path.rglob("*.ndjson"):
                    if any(part in self.ignored_directories for part in ndjson_file.parts):
                        continue
                    loaded_count = self.knowledge_agent.load_ndjson(ndjson_file)
                    total_loaded += loaded_count
                    logger.info(f"Loaded {loaded_count} documents from {ndjson_file.name}")

                source.document_count = total_loaded
                source.last_loaded = datetime.now()
                logger.info(f"Total loaded {total_loaded} documents from {source.name}")

            # Notify callbacks
            self._notify_source_loaded(source)

        except Exception as e:
            logger.error(f"Error loading source {source.name}: {e}")

    async def _watch_for_changes(self) -> None:
        """Watch for changes in knowledge sources."""

        if awatch is None or DefaultFilter is None:
            await self._poll_for_changes()
            return

        watch_targets = self._resolve_watch_targets()
        if not watch_targets:
            await self._poll_for_changes()
            return

        watch_filter = _KnowledgeWatchFilter(self.ignored_directories)
        debounce = self.watch_interval or 30

        async for changes in awatch(*watch_targets, watch_filter=watch_filter, step=debounce):
            if not self.is_running:
                break

            touched_sources = {
                self._resolve_source_from_path(Path(changed_path)) for _, changed_path in changes
            }

            for source in filter(None, touched_sources):
                if source.enabled and source.auto_reload:
                    await self._load_source(source)

    async def _poll_for_changes(self) -> None:
        """Fallback polling when watchfiles is unavailable."""

        while self.is_running:
            try:
                for source in self.sources:
                    if source.enabled and source.auto_reload:
                        await self._check_source_changes(source)

                await asyncio.sleep(self.watch_interval or 30)

            except Exception as exc:  # pragma: no cover - logging path
                logger.error(f"Error in change detection: {exc}")
                await asyncio.sleep(10)

    async def _check_source_changes(self, source: KnowledgeSource) -> None:
        """Check if a knowledge source has changed."""

        try:
            if source.path.is_file():
                # Check file modification time
                if (
                    source.last_loaded is None
                    or source.path.stat().st_mtime > source.last_loaded.timestamp()
                ):
                    logger.info(f"Source {source.name} changed, reloading...")
                    await self._load_source(source)

            elif source.path.is_dir():
                # Check for new or modified NDJSON files
                for ndjson_file in source.path.rglob("*.ndjson"):
                    if any(part in self.ignored_directories for part in ndjson_file.parts):
                        continue
                    if (
                        source.last_loaded is None
                        or ndjson_file.stat().st_mtime > source.last_loaded.timestamp()
                    ):
                        logger.info(f"New/modified file in {source.name}: {ndjson_file.name}")
                        await self._load_source(source)
                        break

        except Exception as e:
            logger.error(f"Error checking changes for {source.name}: {e}")

    def _resolve_watch_targets(self) -> List[Path]:
        """Determine which paths should be passed to the watcher."""

        targets: List[Path] = []
        for source in self.sources:
            if not (source.enabled and source.auto_reload):
                continue
            if source.path.exists():
                targets.append(source.path)
        return targets

    def _resolve_source_from_path(self, candidate: Path) -> Optional[KnowledgeSource]:
        """Map a changed path back to its configured knowledge source."""

        for source in self.sources:
            if candidate == source.path:
                return source

            if source.path.is_dir():
                try:
                    if candidate.is_relative_to(source.path):
                        return source
                except ValueError:
                    continue

        return None

    def add_source(self, source: KnowledgeSource) -> None:
        """Add a new knowledge source."""

        self.sources.append(source)
        logger.info(f"Added knowledge source: {source.name}")

    def _resolve_watch_interval(self) -> Optional[int]:
        raw_value = os.getenv("KNOWLEDGE_WATCH_INTERVAL")
        if raw_value is None or raw_value.strip() == "":
            # Default to no watcher so contributors do not pay the cost unless they opt in.
            return None

        try:
            interval = int(raw_value)
        except ValueError:
            logger.warning(
                "Invalid KNOWLEDGE_WATCH_INTERVAL '%s'; disabling change watcher",
                raw_value,
            )
            return None

        return interval if interval > 0 else None

    async def refresh_all_sources(self) -> None:
        """Reload every enabled knowledge source immediately."""

        await self._load_all_sources()

    def remove_source(self, source_name: str) -> bool:
        """Remove a knowledge source."""

        for i, source in enumerate(self.sources):
            if source.name == source_name:
                self.sources.pop(i)
                logger.info(f"Removed knowledge source: {source_name}")
                return True

        return False

    def enable_source(self, source_name: str) -> bool:
        """Enable a knowledge source."""

        for source in self.sources:
            if source.name == source_name:
                source.enabled = True
                logger.info(f"Enabled knowledge source: {source_name}")
                return True

        return False

    def disable_source(self, source_name: str) -> bool:
        """Disable a knowledge source."""

        for source in self.sources:
            if source.name == source_name:
                source.enabled = False
                logger.info(f"Disabled knowledge source: {source_name}")
                return True

        return False

    def get_source_stats(self) -> Dict[str, Any]:
        """Get statistics about knowledge sources."""

        total_documents = sum(source.document_count for source in self.sources)
        enabled_sources = len([s for s in self.sources if s.enabled])

        return {
            "total_sources": len(self.sources),
            "enabled_sources": enabled_sources,
            "total_documents": total_documents,
            "agent_documents": len(self.knowledge_agent.documents()),
            "sources": [
                {
                    "name": source.name,
                    "path": str(source.path),
                    "enabled": source.enabled,
                    "document_count": source.document_count,
                    "last_loaded": source.last_loaded.isoformat() if source.last_loaded else None,
                    "auto_reload": source.auto_reload,
                    "priority": source.priority,
                }
                for source in self.sources
            ],
        }

    def subscribe_to_changes(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Subscribe to knowledge source change notifications."""

        self.watch_callbacks.append(callback)
        logger.info("Subscribed to knowledge changes")

    def _notify_source_loaded(self, source: KnowledgeSource) -> None:
        """Notify subscribers of source loading."""

        for callback in self.watch_callbacks:
            try:
                callback(
                    "source_loaded",
                    {
                        "source_name": source.name,
                        "document_count": source.document_count,
                        "timestamp": source.last_loaded.isoformat() if source.last_loaded else None,
                    },
                )
            except Exception as e:
                logger.error(f"Error in change notification: {e}")

    async def query_knowledge(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Query the knowledge base."""

        try:
            result = self.knowledge_agent.perform_task(
                {"action": "query", "payload": {"query": query, "limit": limit}}
            )

            return {
                "query": query,
                "results": result.get("outputs", {}).get("answers", []),
                "metrics": result.get("metrics", {}),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error querying knowledge: {e}")
            return {"error": str(e)}

    def stop_auto_loading(self) -> None:
        """Stop automatic knowledge loading."""

        if not self.is_running:
            return

        self.is_running = False
        if self._watch_task and not self._watch_task.done():
            self._watch_task.cancel()
        self._watch_task = None
        logger.info("Stopped knowledge auto-loading")


# Global auto-loader instance
_global_auto_loader: Optional[KnowledgeAutoLoader] = None


def get_auto_loader() -> KnowledgeAutoLoader:
    """Get the global auto-loader instance."""
    global _global_auto_loader
    if _global_auto_loader is None:
        # Create knowledge agent
        event_bus = QAEventBus()
        rules = QARules(version="1.0", agents={}, macros={})
        qa_engine = QAEngine(rules)
        knowledge_agent = KnowledgeAgent(qa_engine, event_bus)

        _global_auto_loader = KnowledgeAutoLoader(knowledge_agent)
    return _global_auto_loader


async def start_knowledge_auto_loading() -> None:
    """Start knowledge auto-loading."""

    if os.getenv("KNOWLEDGE_AUTO_LOAD", "true").lower() in {"0", "false", "off"}:
        logger.info("Knowledge auto-loading disabled via KNOWLEDGE_AUTO_LOAD")
        return

    auto_loader = get_auto_loader()
    await auto_loader.start_auto_loading()


async def get_knowledge_entries() -> List[Dict[str, Any]]:
    """Get all knowledge entries from the auto-loader."""

    auto_loader = get_auto_loader()

    # Return knowledge entries in a format that can be used
    entries = []
    for source in auto_loader.sources:
        if source.enabled and source.document_count > 0:
            entries.append(
                {
                    "name": source.name,
                    "path": str(source.path),
                    "document_count": source.document_count,
                    "last_loaded": source.last_loaded.isoformat() if source.last_loaded else None,
                }
            )

    return entries


async def refresh_knowledge_sources() -> None:
    """Force a reload of every enabled knowledge source."""

    auto_loader = get_auto_loader()
    await auto_loader.refresh_all_sources()


# Export main classes and functions
__all__ = [
    "KnowledgeAutoLoader",
    "KnowledgeSource",
    "get_auto_loader",
    "start_knowledge_auto_loading",
    "refresh_knowledge_sources",
    "get_knowledge_entries",
]
