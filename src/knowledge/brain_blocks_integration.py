"""
Brain Blocks Integration
Integrates Brain Blocks NDJSON data with Knowledge Agent for intelligent querying.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agents.specialist_agents import KnowledgeAgent, KnowledgeDocument
from qa.qa_engine import QAEngine, QARules
from qa.qa_event_bus import QAEventBus

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())


@dataclass
class BrainBlock:
    """Represents a single brain block from NDJSON data."""

    doc_id: str
    title: str
    content: str
    section: str
    tags: List[str]
    hash: str
    updated_at: str
    section_index: int
    chunk_index: int
    chunk_total: int


@dataclass
class BrainBlockQuery:
    """Query for brain blocks."""

    query: str
    limit: int = 5
    section_filter: Optional[str] = None
    tag_filter: Optional[List[str]] = None
    date_range: Optional[Tuple[datetime, datetime]] = None


class BrainBlocksIntegration:
    """Integrates Brain Blocks NDJSON data with Knowledge Agent."""

    def __init__(self, knowledge_agent: KnowledgeAgent):
        self.knowledge_agent = knowledge_agent
        self.brain_blocks: List[BrainBlock] = []
        self.is_loaded = False
        self.load_stats: Dict[str, Any] = {}

    async def load_brain_blocks(self, ndjson_path: Path) -> int:
        """Load brain blocks from NDJSON file."""

        logger.info(f"Loading brain blocks from {ndjson_path}")

        if not ndjson_path.exists():
            logger.error(f"Brain blocks file not found: {ndjson_path}")
            return 0

        try:
            loaded_count = 0
            with open(ndjson_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue

                    try:
                        data = json.loads(line)
                        brain_block = self._parse_brain_block(data, line_num)
                        if brain_block:
                            self.brain_blocks.append(brain_block)

                            # Convert to KnowledgeDocument and add to agent
                            doc = self._convert_to_knowledge_document(brain_block)
                            self.knowledge_agent.ingest_documents([doc])

                            loaded_count += 1

                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON on line {line_num}: {e}")
                        continue
                    except Exception as e:
                        logger.warning(f"Error parsing line {line_num}: {e}")
                        continue

            self.is_loaded = True
            self.load_stats = {
                "file_path": str(ndjson_path),
                "total_blocks": loaded_count,
                "loaded_at": datetime.now().isoformat(),
                "file_size": ndjson_path.stat().st_size,
            }

            logger.info(f"Successfully loaded {loaded_count} brain blocks")
            return loaded_count

        except Exception as e:
            logger.error(f"Error loading brain blocks: {e}")
            return 0

    def _parse_brain_block(self, data: Dict[str, Any], line_num: int) -> Optional[BrainBlock]:
        """Parse a single brain block from JSON data."""

        try:
            return BrainBlock(
                doc_id=data.get("doc_id", f"line_{line_num}"),
                title=data.get("title", ""),
                content=data.get("text", ""),
                section=data.get("section", ""),
                tags=data.get("tags", []),
                hash=data.get("hash", ""),
                updated_at=data.get("updated_at", ""),
                section_index=data.get("section_index", 0),
                chunk_index=data.get("chunk_index", 0),
                chunk_total=data.get("chunk_total", 1),
            )
        except Exception as e:
            logger.warning(f"Error parsing brain block on line {line_num}: {e}")
            return None

    def _convert_to_knowledge_document(self, brain_block: BrainBlock) -> KnowledgeDocument:
        """Convert BrainBlock to KnowledgeDocument."""

        # Create comprehensive content
        content = f"""
Title: {brain_block.title}
Section: {brain_block.section}
Content: {brain_block.content}
Tags: {', '.join(brain_block.tags)}
Updated: {brain_block.updated_at}
Section Index: {brain_block.section_index}
Chunk: {brain_block.chunk_index}/{brain_block.chunk_total}
Hash: {brain_block.hash}
        """.strip()

        return KnowledgeDocument(
            identifier=brain_block.doc_id,
            title=brain_block.title,
            content=content,
            tags=tuple(brain_block.tags),
        )

    async def query_brain_blocks(self, query: BrainBlockQuery) -> List[Dict[str, Any]]:
        """Query brain blocks with advanced filtering."""

        if not self.is_loaded:
            logger.warning("Brain blocks not loaded, loading now...")
            await self._auto_load_brain_blocks()

        # Use knowledge agent for querying
        try:
            result = self.knowledge_agent.perform_task(
                {"action": "query", "payload": {"query": query.query, "limit": query.limit}}
            )

            answers = result.get("outputs", {}).get("answers", [])

            # Apply additional filters
            filtered_answers = self._apply_filters(answers, query)

            return filtered_answers

        except Exception as e:
            logger.error(f"Error querying brain blocks: {e}")
            return []

    def _apply_filters(
        self, answers: List[Dict[str, Any]], query: BrainBlockQuery
    ) -> List[Dict[str, Any]]:
        """Apply additional filters to query results."""

        filtered = answers

        # Filter by section
        if query.section_filter:
            filtered = [
                a for a in filtered if query.section_filter.lower() in a.get("snippet", "").lower()
            ]

        # Filter by tags
        if query.tag_filter:
            filtered = [
                a for a in filtered if any(tag in a.get("tags", []) for tag in query.tag_filter)
            ]

        # Filter by date range
        if query.date_range:
            start_date, end_date = query.date_range
            filtered = [a for a in filtered if self._is_in_date_range(a, start_date, end_date)]

        return filtered[: query.limit]

    def _is_in_date_range(
        self, answer: Dict[str, Any], start_date: datetime, end_date: datetime
    ) -> bool:
        """Check if answer is within date range."""

        # This would need to parse dates from the answer content
        # For now, return True (no date filtering)
        return True

    async def get_brain_block_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded brain blocks."""

        if not self.is_loaded:
            return {"error": "Brain blocks not loaded"}

        # Analyze brain blocks
        sections: Dict[str, int] = {}
        tag_counts: Dict[str, int] = {}
        total_content_length = 0

        for block in self.brain_blocks:
            # Count sections
            section = block.section
            sections[section] = sections.get(section, 0) + 1

            # Count tags
            for tag in block.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Sum content length
            total_content_length += len(block.content)

        return {
            "total_blocks": len(self.brain_blocks),
            "sections": {
                "count": len(sections),
                "top_sections": sorted(sections.items(), key=lambda item: item[1], reverse=True)[
                    :10
                ],
            },
            "tags": {
                "count": len(tag_counts),
                "top_tags": sorted(tag_counts.items(), key=lambda item: item[1], reverse=True)[:20],
            },
            "content": {
                "total_length": total_content_length,
                "average_length": (
                    total_content_length / len(self.brain_blocks) if self.brain_blocks else 0
                ),
            },
            "load_stats": self.load_stats,
        }

    async def search_by_section(self, section_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search brain blocks by section."""

        query = BrainBlockQuery(query=section_name, limit=limit, section_filter=section_name)

        return await self.query_brain_blocks(query)

    async def search_by_tags(self, tags: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search brain blocks by tags."""

        query = BrainBlockQuery(query=" ".join(tags), limit=limit, tag_filter=tags)

        return await self.query_brain_blocks(query)

    async def get_recent_blocks(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently updated brain blocks."""

        # This would need proper date parsing
        query = BrainBlockQuery(query="recent updates", limit=limit)

        return await self.query_brain_blocks(query)

    async def _auto_load_brain_blocks(self) -> None:
        """Automatically load brain blocks if not already loaded."""

        # Try to find brain blocks files
        possible_paths = [
            Path("Brain docs cleansed .ndjson"),
            Path("Bundle cleansed .ndjson"),
            Path(".").glob("**/*.ndjson"),
        ]

        for path in possible_paths:
            if isinstance(path, Path) and path.exists():
                await self.load_brain_blocks(path)
                break
            elif hasattr(path, "__iter__"):
                for p in path:
                    if p.exists():
                        await self.load_brain_blocks(p)
                        break

    async def export_brain_blocks(self, output_path: Path) -> None:
        """Export brain blocks data."""

        data = {
            "brain_blocks": [
                {
                    "doc_id": block.doc_id,
                    "title": block.title,
                    "section": block.section,
                    "tags": block.tags,
                    "content_preview": (
                        block.content[:200] + "..." if len(block.content) > 200 else block.content
                    ),
                    "updated_at": block.updated_at,
                    "section_index": block.section_index,
                    "chunk_index": block.chunk_index,
                    "chunk_total": block.chunk_total,
                }
                for block in self.brain_blocks
            ],
            "stats": await self.get_brain_block_stats(),
            "exported_at": datetime.now().isoformat(),
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported brain blocks data to {output_path}")


# Global brain blocks integration instance
_global_brain_blocks: Optional[BrainBlocksIntegration] = None


def get_brain_blocks_integration() -> BrainBlocksIntegration:
    """Get the global brain blocks integration instance."""
    global _global_brain_blocks
    if _global_brain_blocks is None:
        # Create knowledge agent
        event_bus = QAEventBus()
        rules = QARules(version="1.0", agents={}, macros={})
        qa_engine = QAEngine(rules)
        knowledge_agent = KnowledgeAgent(qa_engine, event_bus)

        _global_brain_blocks = BrainBlocksIntegration(knowledge_agent)
    return _global_brain_blocks


async def start_brain_blocks_integration() -> None:
    """Start brain blocks integration."""

    integration = get_brain_blocks_integration()
    await integration._auto_load_brain_blocks()


async def query_brain_blocks(query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
    """Query brain blocks and return results."""

    integration = get_brain_blocks_integration()
    # Create a BrainBlockQuery object
    from .brain_blocks_integration import BrainBlockQuery

    query_obj = BrainBlockQuery(query=query, limit=limit)
    results = await integration.query_brain_blocks(query_obj)

    return [
        {
            "doc_id": block.get("doc_id"),
            "title": block.get("title"),
            "content": block.get("content") or block.get("snippet"),
            "section": block.get("section"),
            "tags": block.get("tags", []),
            "updated_at": block.get("updated_at"),
        }
        for block in results
    ]


# Export main classes and functions
__all__ = [
    "BrainBlocksIntegration",
    "BrainBlock",
    "BrainBlockQuery",
    "get_brain_blocks_integration",
    "start_brain_blocks_integration",
    "query_brain_blocks",
]
