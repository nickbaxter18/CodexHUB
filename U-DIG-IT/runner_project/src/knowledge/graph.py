"""Knowledge graph utilities for Stage 2."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

try:
    import networkx as nx
except ImportError:  # pragma: no cover - exercised when dependency missing
    nx = None

    class _NodeView:
        """Lightweight stand-in for :class:`networkx.classes.reportviews.NodeView`."""

        def __init__(self, graph: "_FallbackDiGraph") -> None:
            self._graph = graph

        def __iter__(self) -> Iterator[str]:
            return iter(self._graph._nodes)

        def __len__(self) -> int:
            return len(self._graph._nodes)

        def __getitem__(self, node: str) -> Dict[str, object]:
            return self._graph._nodes[node]

        def __call__(
            self, data: bool = False, default: Optional[Dict[str, object]] = None
        ) -> Iterator[Tuple[str, Dict[str, object]]]:
            if not data:
                return ((node, {}) for node in self._graph._nodes)
            if default is None:
                return ((node, self._graph._nodes[node]) for node in self._graph._nodes)
            return (
                (
                    node,
                    self._graph._nodes[node] if node in self._graph._nodes else default,
                )
                for node in self._graph._nodes
            )

    class _FallbackDiGraph:
        """Minimal directed graph implementation used when NetworkX is unavailable."""

        def __init__(self) -> None:
            self._nodes: Dict[str, Dict[str, object]] = {}
            self._successors: Dict[str, set[str]] = {}
            self._predecessors: Dict[str, set[str]] = {}
            self._edge_count = 0

        def add_node(self, node: str, **attrs: object) -> None:
            stored = self._nodes.setdefault(node, {})
            stored.update(attrs)
            self._successors.setdefault(node, set())
            self._predecessors.setdefault(node, set())

        def add_edge(self, source: str, target: str) -> None:
            if source not in self._nodes:
                self.add_node(source)
            if target not in self._nodes:
                self.add_node(target)
            if target not in self._successors[source]:
                self._successors[source].add(target)
                self._predecessors[target].add(source)
                self._edge_count += 1

        def number_of_nodes(self) -> int:
            return len(self._nodes)

        def number_of_edges(self) -> int:
            return self._edge_count

        def successors(self, node: str) -> Iterator[str]:
            return iter(self._successors.get(node, set()))

        def predecessors(self, node: str) -> Iterator[str]:
            return iter(self._predecessors.get(node, set()))

        def __contains__(self, node: object) -> bool:
            return node in self._nodes

        @property
        def nodes(self) -> _NodeView:
            return _NodeView(self)

    def _create_graph() -> Any:
        return _FallbackDiGraph()

else:  # pragma: no cover - executed in environments with networkx installed

    def _create_graph() -> Any:
        return nx.DiGraph()


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
            str(value) for value in self.metadata.values() if value not in (None, "")
        )
        if description:
            components.append(description)
        return "\n".join(component for component in components if component)


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


def _as_tag_tuple(raw_tags: object) -> Tuple[str, ...]:
    if raw_tags in (None, ""):
        return ()
    if isinstance(raw_tags, (list, tuple, set)):
        return tuple(str(tag) for tag in raw_tags if tag not in (None, ""))
    return (str(raw_tags),)


def _normalise_entry(entry: Dict[str, object]) -> KnowledgeRecord:
    identifier = str(
        entry.get("doc_id") or entry.get("id") or entry.get("slug") or entry.get("hash")
    )
    if not identifier:
        raise KnowledgeError("Entry is missing an identifier")
    title = str(entry.get("title") or entry.get("section") or identifier)
    text = str(entry.get("text") or entry.get("content") or "")
    tags = _as_tag_tuple(entry.get("tags"))
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
        self.graph: Any = _create_graph()

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
        if limit <= 0:
            return []
        query_lower = text.lower()
        scored: List[Tuple[float, str]] = []
        for node, data in self.graph.nodes(data=True):
            title = str(data.get("title", ""))
            body = str(data.get("text", ""))
            tags = _as_tag_tuple(data.get("tags", ()))
            metadata = data.get("metadata", {})
            metadata_values: Tuple[str, ...]
            if isinstance(metadata, dict):
                metadata_values = tuple(
                    str(value) for value in metadata.values() if value not in (None, "")
                )
            else:
                metadata_values = (str(metadata),) if metadata not in (None, "") else ()
            searchable = " ".join(
                component
                for component in (
                    title,
                    body,
                    " ".join(tags),
                    " ".join(metadata_values),
                )
                if component
            )
            searchable_lower = searchable.lower()
            if query_lower in searchable_lower:
                score = searchable_lower.count(query_lower) + 0.1 * float(len(tags))
                scored.append((float(score), node))
        scored.sort(key=lambda item: (-item[0], item[1]))
        results: List[Dict[str, object]] = []
        for score, node in scored[:limit]:
            data = self.graph.nodes[node]
            text_value = str(data.get("text", ""))
            location = text_value.lower().find(query_lower)
            if location >= 0:
                start = max(0, location - 60)
                end = min(len(text_value), location + 120)
                snippet = text_value[start:end]
            else:
                snippet = text_value
            tags_list = list(_as_tag_tuple(data.get("tags", ())))
            metadata_attr = data.get("metadata", {})
            if isinstance(metadata_attr, dict):
                metadata_payload: Dict[str, object] = dict(metadata_attr)
            elif metadata_attr in (None, ""):
                metadata_payload = {}
            else:
                metadata_payload = {"value": metadata_attr}
            results.append(
                {
                    "id": node,
                    "title": data.get("title"),
                    "score": score,
                    "snippet": snippet.strip(),
                    "tags": tags_list,
                    "metadata": metadata_payload,
                }
            )
        return results

    def neighbours(self, identifier: str, depth: int = 1) -> List[str]:
        if identifier not in self.graph:
            raise KnowledgeError(f"Unknown node requested: {identifier}")
        visited = {identifier}
        frontier = {identifier}
        for _ in range(depth):
            next_frontier: set[str] = set()
            for node in frontier:
                next_frontier.update(self.graph.successors(node))
                next_frontier.update(self.graph.predecessors(node))
            next_frontier -= visited
            visited.update(next_frontier)
            frontier = next_frontier
        visited.remove(identifier)
        return sorted(visited)

    def add_or_update(self, record: KnowledgeRecord) -> None:
        self.add_record(record)

    def stats(self) -> Dict[str, int]:
        """Return the number of nodes and edges contained in the graph."""

        return {
            "nodes": int(self.graph.number_of_nodes()),
            "edges": int(self.graph.number_of_edges()),
        }
