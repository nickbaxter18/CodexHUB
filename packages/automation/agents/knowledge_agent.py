"""
SECTION 1: Header & Purpose
- Implements the ``KnowledgeAgent`` responsible for intelligence amplification across CodexHUB.
- Provides a governance-aware retrieval pipeline over Brain Blocks and NDJSON knowledge bundles.
- Ensures each query yields auditable metrics (coverage, latency, recall proxy) for QA oversight.
"""

from __future__ import annotations

# SECTION 2: Imports / Dependencies
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterable, Iterator, List, Sequence, Tuple

from agents.agent_base import Agent

if TYPE_CHECKING:
    from qa.qa_engine import QAEngine
    from qa.qa_event_bus import QAEventBus


# SECTION 3: Types / Interfaces / Schemas


@dataclass(frozen=True)
class KnowledgeRecord:
    """Canonical representation of a single knowledge entry."""

    doc_id: str
    title: str
    text: str
    tags: Tuple[str, ...] = field(default_factory=tuple)
    section_path: str | None = None
    source_path: Path | None = None
    _text_normalised: str = field(init=False, repr=False)
    _title_normalised: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_text_normalised", self.text.lower())
        object.__setattr__(self, "_title_normalised", self.title.lower())

    def matches_tags(self, required_tags: Iterable[str]) -> bool:
        """Return ``True`` when the record includes all ``required_tags``."""

        tag_set = {tag.lower() for tag in self.tags}
        return all(tag.lower() in tag_set for tag in required_tags)


@dataclass(frozen=True)
class KnowledgeSearchResult:
    """Aggregated search outcome surfaced to downstream agents."""

    record: KnowledgeRecord
    score: float
    matched_terms: Tuple[str, ...]
    snippet: str

    def to_payload(self) -> Dict[str, Any]:
        """Return a JSON-serialisable payload for QA reporting."""

        return {
            "doc_id": self.record.doc_id,
            "title": self.record.title,
            "section_path": self.record.section_path,
            "score": self.score,
            "matched_terms": list(self.matched_terms),
            "snippet": self.snippet,
            "tags": list(self.record.tags),
            "source_path": str(self.record.source_path) if self.record.source_path else None,
        }


class KnowledgeStore:
    """Materializes NDJSON/JSON knowledge corpora for retrieval."""

    def __init__(
        self,
        sources: Sequence[Path],
        *,
        max_records: int | None = None,
    ) -> None:
        self._sources = tuple(sources)
        self._max_records = max_records
        self._records: List[KnowledgeRecord] = []
        self._loaded = False

    @property
    def sources(self) -> Tuple[Path, ...]:
        """Return the immutable collection of configured sources."""

        return self._sources

    @property
    def total_records(self) -> int:
        """Return the number of indexed knowledge entries."""

        return len(self._records)

    def ensure_loaded(self) -> None:
        """Load knowledge sources once, enforcing deterministic order."""

        if self._loaded:
            return
        for path in self._sources:
            if not path.exists():
                continue
            loader = self._iter_source(path)
            for record in loader:
                self._records.append(record)
                if self._max_records is not None and len(self._records) >= self._max_records:
                    self._loaded = True
                    return
        self._loaded = True

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        require_tags: Sequence[str] | None = None,
    ) -> List[KnowledgeSearchResult]:
        """Return ranked knowledge matches for ``query``."""

        query = query.strip()
        if not query:
            raise ValueError("query must be a non-empty string")
        if limit <= 0:
            raise ValueError("limit must be a positive integer")

        self.ensure_loaded()
        if not self._records:
            raise RuntimeError("knowledge store contains no records")

        tokens = _tokenize(query)
        if not tokens:
            return []

        required_tags = tuple(tag.strip().lower() for tag in require_tags or () if tag.strip())
        matches: List[KnowledgeSearchResult] = []
        for record in self._records:
            if required_tags and not record.matches_tags(required_tags):
                continue
            score, matched_terms = _score_record(record, tokens)
            if score == 0.0:
                continue
            snippet = _build_snippet(record.text, matched_terms)
            matches.append(
                KnowledgeSearchResult(
                    record=record,
                    score=score,
                    matched_terms=matched_terms,
                    snippet=snippet,
                )
            )

        matches.sort(key=lambda result: (-result.score, result.record.title, result.record.doc_id))
        return matches[:limit]

    def _iter_source(self, path: Path) -> Iterator[KnowledgeRecord]:
        """Yield records parsed from ``path`` while handling NDJSON and JSON."""

        if path.suffix.lower() in {".ndjson", ".jsonl"} or path.name.endswith(".ndjson"):
            yield from self._iter_ndjson(path)
        elif path.suffix.lower() == ".json":
            yield from self._iter_json(path)

    def _iter_ndjson(self, path: Path) -> Iterator[KnowledgeRecord]:
        """Yield records from an NDJSON file."""

        with path.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                yield self._create_record(payload, path, fallback_suffix=str(index))

    def _iter_json(self, path: Path) -> Iterator[KnowledgeRecord]:
        """Yield records from a JSON list file."""

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        if isinstance(payload, list):
            for index, entry in enumerate(payload):
                if not isinstance(entry, dict):
                    continue
                yield self._create_record(entry, path, fallback_suffix=str(index))

    def _create_record(
        self,
        payload: Dict[str, Any],
        source_path: Path,
        *,
        fallback_suffix: str,
    ) -> KnowledgeRecord:
        """Normalise payload dictionaries into ``KnowledgeRecord`` instances."""

        doc_id = str(
            payload.get("doc_id") or payload.get("id") or f"{source_path.name}:{fallback_suffix}"
        )
        title = str(payload.get("title") or payload.get("section") or doc_id)
        text = str(payload.get("text") or payload.get("content") or "")
        section_path = payload.get("section_path")
        if section_path is not None:
            section_path = str(section_path)
        raw_tags = payload.get("tags")
        tags: Tuple[str, ...]
        if isinstance(raw_tags, (list, tuple)):
            tags = tuple(str(tag) for tag in raw_tags if isinstance(tag, (str, int, float)))
        else:
            tags = ()

        return KnowledgeRecord(
            doc_id=doc_id,
            title=title,
            text=text,
            tags=tags,
            section_path=section_path,
            source_path=source_path,
        )


# SECTION 4: Core Logic / Implementation


class KnowledgeAgent(Agent):
    """QA-governed knowledge retrieval agent."""

    DEFAULT_LIMIT = 5

    def __init__(
        self,
        name: str,
        qa_engine: QAEngine,
        event_bus: QAEventBus,
        sources: Sequence[Path],
        *,
        max_records: int | None = None,
    ) -> None:
        super().__init__(name, qa_engine, event_bus)
        self.store = KnowledgeStore(sources, max_records=max_records)

    def perform_task(
        self,
        query: str,
        *,
        limit: int | None = None,
        require_tags: Sequence[str] | None = None,
    ) -> Dict[str, Any]:
        """Execute a retrieval query and surface governance metrics."""

        effective_limit = limit or self.DEFAULT_LIMIT
        start_time = time.perf_counter()
        results = self.store.search(query, limit=effective_limit, require_tags=require_tags)
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        total_records = self.store.total_records
        coverage_ratio = len(results) / total_records if total_records else 0.0

        payload: Dict[str, Any] = {
            "query": query,
            "results": [result.to_payload() for result in results],
            "results_found": len(results),
            "coverage_ratio": coverage_ratio,
            "latency_ms": latency_ms,
            "total_records": total_records,
            "sources_indexed": [str(path) for path in self.store.sources if path.exists()],
            "tests_executed": list(self.required_tests()),
        }
        if require_tags:
            payload["required_tags"] = [tag for tag in require_tags if tag.strip()]
        if results:
            payload["top_result"] = results[0].to_payload()
        return payload


# SECTION 5: Error & Edge Case Handling
# - ``KnowledgeStore.search`` validates empty queries and zero limits early.
# - Empty corpora raise ``RuntimeError`` to ensure QA marks the run as a failure.
# - JSON decoding errors are ignored per record to maximise resilience across large corpora.


# SECTION 6: Performance Considerations
# - The store loads sources once per process and supports ``max_records`` to constrain memory.
# - Search uses simple token frequency scoring to remain CPU friendly.
# - Future iterations can swap in vector indexes without altering the public API.


# SECTION 7: Exports / Public API
__all__ = ["KnowledgeAgent", "KnowledgeRecord", "KnowledgeSearchResult", "KnowledgeStore"]


# SECTION 8: Internal Utilities


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]{2,}")


def _tokenize(query: str) -> Tuple[str, ...]:
    """Split ``query`` into lowercase alphanumeric tokens."""

    return tuple(match.group(0).lower() for match in TOKEN_PATTERN.finditer(query))


def _score_record(
    record: KnowledgeRecord, tokens: Tuple[str, ...]
) -> Tuple[float, Tuple[str, ...]]:
    """Return (score, matched_terms) for ``record`` given ``tokens``."""

    matched_terms: List[str] = []
    score = 0.0
    for token in tokens:
        token_score = record._title_normalised.count(token) * 2 + record._text_normalised.count(
            token
        )
        if token_score:
            matched_terms.append(token)
            score += float(token_score)
    return score, tuple(dict.fromkeys(matched_terms))


def _build_snippet(text: str, terms: Tuple[str, ...], *, window: int = 120) -> str:
    """Return a text snippet around the earliest matched term."""

    if not terms:
        return text[:window].strip()
    lower = text.lower()
    first_index = min((lower.find(term) for term in terms if lower.find(term) != -1), default=-1)
    if first_index == -1:
        return text[:window].strip()
    start = max(first_index - window // 2, 0)
    end = min(start + window, len(text))
    snippet = text[start:end]
    return snippet.strip()
