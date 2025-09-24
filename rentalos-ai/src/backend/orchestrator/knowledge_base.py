"""In-memory knowledge base used to mimic a Neo4j integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, MutableMapping, Sequence


@dataclass
class RelationshipRecord:
    """Represents an edge in the lightweight knowledge graph."""

    subject: str
    predicate: str
    target: str


@dataclass
class MetricSeries:
    """Stores the latest metric values for an entity."""

    values: List[float] = field(default_factory=list)

    def append(self, value: float, max_points: int = 30) -> None:
        self.values.append(float(value))
        if len(self.values) > max_points:
            # Retain a rolling window so calculations stay responsive.
            del self.values[: len(self.values) - max_points]

    def tail(self, limit: int | None = None) -> List[float]:
        if limit is None:
            return list(self.values)
        if limit <= 0:
            return []
        return list(self.values[-limit:])


class KnowledgeBaseClient:
    """Lightweight graph client that mirrors core Neo4j queries."""

    def __init__(self) -> None:
        self._relationships: List[RelationshipRecord] = []
        self._metrics: MutableMapping[str, MutableMapping[str, MetricSeries]] = {}

    # ------------------------------------------------------------------
    # Relationship helpers
    # ------------------------------------------------------------------
    def add_relationship(self, subject: str, predicate: str, target: str) -> None:
        self._relationships.append(
            RelationshipRecord(subject=subject, predicate=predicate, target=target)
        )

    def related(self, subject: str, predicate: str | None = None) -> List[str]:
        matches: Iterable[RelationshipRecord]
        if predicate is None:
            matches = (rel for rel in self._relationships if rel.subject == subject)
        else:
            matches = (
                rel
                for rel in self._relationships
                if rel.subject == subject and rel.predicate == predicate
            )
        return [rel.target for rel in matches]

    # ------------------------------------------------------------------
    # Metric helpers
    # ------------------------------------------------------------------
    def record_metric(self, entity: str, metric: str, value: float) -> None:
        entity_metrics = self._metrics.setdefault(entity, {})
        series = entity_metrics.setdefault(metric, MetricSeries())
        series.append(value)

    def get_metric_series(self, entity: str, metric: str, limit: int | None = None) -> List[float]:
        entity_metrics = self._metrics.get(entity)
        if not entity_metrics:
            return []
        series = entity_metrics.get(metric)
        if not series:
            return []
        return series.tail(limit)

    def latest_metric(self, entity: str, metric: str) -> float | None:
        series = self.get_metric_series(entity, metric, limit=1)
        return series[-1] if series else None

    def snapshot(self) -> Dict[str, Dict[str, Sequence[float]]]:
        """Return a serializable snapshot for debugging and tests."""

        return {
            entity: {metric: list(series.values) for metric, series in metrics.items()}
            for entity, metrics in self._metrics.items()
        }

    def clear(self) -> None:
        """Remove all stored relationships and metrics (testing helper)."""

        self._relationships.clear()
        self._metrics.clear()


knowledge_base = KnowledgeBaseClient()
