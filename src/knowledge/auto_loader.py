"""
Knowledge Auto-Loader
Automatically loads NDJSON data into Knowledge Agent and keeps it synchronized.
"""

from __future__ import annotations

import asyncio
import json
import logging

# Import Knowledge Agent
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.specialist_agents import KnowledgeAgent, KnowledgeDocument
from qa.qa_engine import QAEngine, QARules
from qa.qa_event_bus import QAEventBus

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


class KnowledgeAutoLoader:
    """Automatically loads and manages knowledge sources for the Knowledge Agent."""

    def __init__(self, knowledge_agent: KnowledgeAgent):
        self.knowledge_agent = knowledge_agent
        self.sources: List[KnowledgeSource] = []
        self.is_running = False
        self.watch_callbacks: List[Callable] = []

        # Setup default sources
        self._setup_default_sources()

    def _setup_default_sources(self) -> None:
        """Setup default knowledge sources."""

        default_sources = [
            # Brain docs cleansed NDJSON
            KnowledgeSource(
                name="brain_docs", path=Path("Brain docs cleansed .ndjson"), priority=1
            ),
            # Bundle cleansed NDJSON
            KnowledgeSource(name="bundle_docs", path=Path("Bundle cleansed .ndjson"), priority=2),
            # Any other NDJSON files in the repository
            KnowledgeSource(name="repository_docs", path=Path("."), priority=3),
        ]

        self.sources.extend(default_sources)
        logger.info(f"Setup {len(default_sources)} default knowledge sources")

    async def start_auto_loading(self) -> None:
        """Start automatic knowledge loading."""

        self.is_running = True
        logger.info("Starting knowledge auto-loading")

        # Initial load of all sources
        await self._load_all_sources()

        # Start watching for changes
        await self._watch_for_changes()

    async def _load_all_sources(self) -> None:
        """Load all enabled knowledge sources."""

        for source in self.sources:
            if source.enabled:
                await self._load_source(source)

    async def _load_source(self, source: KnowledgeSource) -> None:
        """Load a specific knowledge source."""

        try:
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

        while self.is_running:
            try:
                # Check for changes in all sources
                for source in self.sources:
                    if source.enabled and source.auto_reload:
                        await self._check_source_changes(source)

                # Wait before next check
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error in change detection: {e}")
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
                    if (
                        source.last_loaded is None
                        or ndjson_file.stat().st_mtime > source.last_loaded.timestamp()
                    ):
                        logger.info(f"New/modified file in {source.name}: {ndjson_file.name}")
                        await self._load_source(source)
                        break

        except Exception as e:
            logger.error(f"Error checking changes for {source.name}: {e}")

    def add_source(self, source: KnowledgeSource) -> None:
        """Add a new knowledge source."""

        self.sources.append(source)
        logger.info(f"Added knowledge source: {source.name}")

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

    def subscribe_to_changes(self, callback: Callable) -> None:
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

        self.is_running = False
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

    auto_loader = get_auto_loader()
    await auto_loader.start_auto_loading()


async def get_knowledge_entries() -> List[Dict[str, Any]]:
    """Get all knowledge entries from the auto-loader."""

    auto_loader = get_auto_loader()
    stats = auto_loader.get_source_stats()

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


# Export main classes and functions
__all__ = [
    "KnowledgeAutoLoader",
    "KnowledgeSource",
    "get_auto_loader",
    "start_knowledge_auto_loading",
    "get_knowledge_entries",
]
