import json
from pathlib import Path
from typing import Any

import pytest

from src import config
from src.knowledge import retrieval


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
    from src.knowledge.graph import KnowledgeRecord

    retrieval.ingest(
        KnowledgeRecord(
            identifier="c", title="Gamma", text="bayesian methods", tags=("math",), metadata={}
        )
    )
    refreshed = retrieval.query("bayesian", limit=1)
    assert refreshed[0]["id"] == "c"

    retrieval.clear_cache()
    config.get_config.cache_clear()
