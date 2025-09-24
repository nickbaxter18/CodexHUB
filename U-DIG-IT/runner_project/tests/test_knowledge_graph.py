import json
from pathlib import Path
from typing import Any

import pytest

from src import config
from src.knowledge import retrieval
from src.knowledge.graph import KnowledgeGraph, KnowledgeRecord


def create_dataset(tmp_path: Path) -> Path:
    path = tmp_path / "data.ndjson"
    entries = [
        {
            "doc_id": "a",
            "title": "Alpha Node",
            "text": "probability and statistics",
            "tags": ["math"],
        },
        {
            "doc_id": "b",
            "title": "Beta Node",
            "text": "statistics overview",
            "links_out": ["a"],
            "tags": ["science"],
        },
    ]
    path.write_text("\n".join(json.dumps(entry) for entry in entries))
    return path


@pytest.mark.asyncio
async def test_query_and_neighbours(monkeypatch: Any, tmp_path: Path) -> None:
    dataset = create_dataset(tmp_path)
    monkeypatch.setenv("RUNNER_KNOWLEDGE_SOURCES", json.dumps([str(dataset)]))
    config.get_config.cache_clear()
    retrieval.clear_cache()

    results = retrieval.query("statistics", limit=2)
    assert len(results) == 2
    assert results[0]["id"] in {"a", "b"}

    neighbours = retrieval.neighbours("b", depth=1)
    assert "a" in neighbours

    # Ingest a new record and ensure it can be queried immediately.
    retrieval.ingest(
        KnowledgeRecord(
            identifier="c", title="Gamma", text="bayesian methods", tags=("math",), metadata={}
        )
    )
    refreshed = retrieval.query("bayesian", limit=1)
    assert refreshed[0]["id"] == "c"

    retrieval.clear_cache()
    config.get_config.cache_clear()


def test_query_uses_metadata_and_deterministic_order() -> None:
    graph = KnowledgeGraph()
    graph.add_record(
        KnowledgeRecord(
            identifier="alpha",
            title="Alpha",
            text="Bayes fundamentals",
            tags=("probability",),
            metadata={"topic": "statistics"},
        )
    )
    graph.add_record(
        KnowledgeRecord(
            identifier="beta",
            title="Beta",
            text="Bayes fundamentals",
            tags=(),
            metadata={"topic": "statistics"},
        )
    )

    results = graph.query("bayes", limit=5)

    assert [item["id"] for item in results[:2]] == ["alpha", "beta"]
    assert results[0]["metadata"] == {"topic": "statistics"}
    assert results[0]["tags"] == ["probability"]


def test_metadata_only_document_matches_query() -> None:
    graph = KnowledgeGraph()
    graph.add_record(
        KnowledgeRecord(
            identifier="meta", title="Meta", text="", tags=(), metadata={"priority": 42}
        )
    )

    results = graph.query("42", limit=1)
    assert results and results[0]["id"] == "meta"


def test_neighbours_sorted_by_identifier() -> None:
    graph = KnowledgeGraph()
    graph.add_record(KnowledgeRecord(identifier="a", title="A", text="root", tags=(), metadata={}))
    graph.add_record(KnowledgeRecord(identifier="b", title="B", text="child", tags=(), metadata={}))
    graph.add_record(KnowledgeRecord(identifier="c", title="C", text="child", tags=(), metadata={}))
    graph.graph.add_edge("a", "b")
    graph.graph.add_edge("c", "a")

    neighbours = graph.neighbours("a", depth=1)
    assert neighbours == ["b", "c"]
