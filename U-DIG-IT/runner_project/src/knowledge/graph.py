"""Knowledge graph utilities for Stage 2."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Tuple

import networkx as nx

from ..errors import KnowledgeError


@dataclass
class KnowledgeRecord:
    """A normalized entry stored in the knowledge graph."""

    identifier: str
    title: str
    text: str
    tags: Tuple[str, ...]
    metadata: Dict[str, object]

    @property
    def searchable_text(self) -> str:
        components = [self.title, self.text, " ".join(self.tags)]
        description = " ".join(
            str(value) for value in self.metadata.values() if isinstance(value, str)
        )
        if description:
            components.append(description)
        return " \n".join(component for component in components if component)


def _read_ndjson(path: Path) -> Iterator[Dict[str, object]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise KnowledgeError(f"Failed to parse NDJSON line in {path}: {exc}") from exc


def _normalise_entry(entry: Dict[str, object]) -> KnowledgeRecord:
    identifier = str(
        entry.get("doc_id") or entry.get("id") or entry.get("slug") or entry.get("hash")
    )
    if not identifier:
        raise KnowledgeError("Entry is missing an identifier")
    title = str(entry.get("title") or entry.get("section") or identifier)
    text = str(entry.get("text") or entry.get("content") or "")
    raw_tags = entry.get("tags") or []
    tags: Tuple[str, ...]
    if isinstance(raw_tags, (list, tuple)):
        tags = tuple(str(tag) for tag in raw_tags)
    else:
        tags = (str(raw_tags),)
    metadata = {
        key: value
        for key, value in entry.items()
        if key
        not in {"doc_id", "id", "slug", "hash", "title", "text", "content", "tags", "links_out"}
    }
    return KnowledgeRecord(
        identifier=identifier, title=title, text=text, tags=tags, metadata=metadata
    )


class KnowledgeGraph:
    """In-memory directed graph capturing knowledge relationships."""

    def __init__(self) -> None:
        self.graph = nx.DiGraph()

    @classmethod
    def from_sources(cls, sources: Iterable[Path]) -> "KnowledgeGraph":
        graph = cls()
        for path in sources:
            if not path.exists():
                continue
            for entry in _read_ndjson(path):
                record = _normalise_entry(entry)
                graph.add_record(record)
                graph._add_links(record.identifier, entry.get("links_out"))
        if graph.graph.number_of_nodes() == 0:
            raise KnowledgeError("Knowledge graph has no nodes; check configured sources")
        return graph

    def add_record(self, record: KnowledgeRecord) -> None:
        self.graph.add_node(
            record.identifier,
            title=record.title,
            text=record.text,
            tags=record.tags,
            metadata=record.metadata,
        )

    def _add_links(self, identifier: str, links_out: object) -> None:
        if not links_out:
            return
        targets: List[str] = []
        if isinstance(links_out, (list, tuple)):
            for item in links_out:
                if isinstance(item, str):
                    targets.append(item)
                elif isinstance(item, dict):
                    candidate = item.get("doc_id") or item.get("slug") or item.get("target")
                    if candidate:
                        targets.append(str(candidate))
        elif isinstance(links_out, str):
            targets.append(links_out)
        for target in targets:
            self.graph.add_edge(identifier, target)

    def query(self, text: str, limit: int = 5) -> List[Dict[str, object]]:
        if not text:
            raise KnowledgeError("Query text cannot be empty")
        query_lower = text.lower()
        scored: List[Tuple[float, str]] = []
        for node, data in self.graph.nodes(data=True):
            searchable = " ".join(
                [data.get("title", ""), data.get("text", ""), " ".join(data.get("tags", ()))]
            )
            searchable_lower = searchable.lower()
            if query_lower in searchable_lower:
                score = searchable_lower.count(query_lower) + 0.1 * len(data.get("tags", ()))
                scored.append((float(score), node))
        scored.sort(key=lambda item: item[0], reverse=True)
        results: List[Dict[str, object]] = []
        for score, node in scored[:limit]:
            data = self.graph.nodes[node]
            snippet = data.get("text", "")
            location = snippet.lower().find(query_lower)
            if location >= 0:
                start = max(0, location - 60)
                end = min(len(snippet), location + 120)
                snippet = snippet[start:end]
            results.append(
                {
                    "id": node,
                    "title": data.get("title"),
                    "score": score,
                    "snippet": snippet.strip(),
                    "tags": list(data.get("tags", ())),
                }
            )
        return results

    def neighbours(self, identifier: str, depth: int = 1) -> List[str]:
        if identifier not in self.graph:
            raise KnowledgeError(f"Unknown node requested: {identifier}")
        visited = {identifier}
        frontier = {identifier}
        for _ in range(depth):
            next_frontier = set()
            for node in frontier:
                next_frontier.update(self.graph.successors(node))
                next_frontier.update(self.graph.predecessors(node))
            next_frontier -= visited
            visited.update(next_frontier)
            frontier = next_frontier
        visited.remove(identifier)
        return list(visited)

    def add_or_update(self, record: KnowledgeRecord) -> None:
        self.add_record(record)

    def stats(self) -> Dict[str, int]:
        """Return the number of nodes and edges contained in the graph."""

        return {
            "nodes": int(self.graph.number_of_nodes()),
            "edges": int(self.graph.number_of_edges()),
        }
