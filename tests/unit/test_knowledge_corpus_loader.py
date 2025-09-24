"""Tests for NDJSON-based knowledge corpus loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from agents import KnowledgeAgent
from knowledge import (
    KnowledgeCorpusLoader,
    bootstrap_repository_knowledge,
    discover_default_knowledge_paths,
)
from qa.qa_engine import QAEngine
from qa.qa_event_bus import QAEventBus


@pytest.fixture(scope="module")
def qa_engine() -> QAEngine:
    config_dir = Path("config")
    return QAEngine.from_files(config_dir / "qa_rules.json", config_dir / "qa_rules.schema.json")


@pytest.fixture()
def event_bus() -> QAEventBus:
    return QAEventBus()


def test_corpus_loader_requires_paths() -> None:
    with pytest.raises(ValueError):
        KnowledgeCorpusLoader([])


def test_loader_ingests_documents(
    tmp_path: Path, qa_engine: QAEngine, event_bus: QAEventBus
) -> None:
    ndjson_file = tmp_path / "knowledge.ndjson"
    ndjson_file.write_text(
        """
{"id": "alpha", "title": "Alpha", "content": "First entry"}
{"id": "beta", "title": "Beta", "content": "Second entry", "tags": ["governance"]}
        """.strip()
    )

    agent = KnowledgeAgent(qa_engine, event_bus)
    loader = KnowledgeCorpusLoader([ndjson_file])
    ingested = loader.load_into_agent(agent)
    assert ingested == 2
    documents = agent.documents()
    assert len(documents) == 2
    assert {doc.identifier for doc in documents} == {"alpha", "beta"}


def test_repository_bootstrap_uses_discovery(
    tmp_path: Path, qa_engine: QAEngine, event_bus: QAEventBus
) -> None:
    ndjson_file = tmp_path / "repository-docs.ndjson"
    ndjson_file.write_text('{"id": "gamma", "title": "Gamma", "content": "Repository entry"}\n')

    agent = KnowledgeAgent(qa_engine, event_bus)
    count = bootstrap_repository_knowledge(agent, root=tmp_path)
    assert count == 1
    answers = agent.perform_task(
        {"action": "query", "payload": {"query": "repository", "limit": 1}}
    )["outputs"]["answers"]
    assert answers and answers[0]["id"].startswith("gamma")

    discovered = discover_default_knowledge_paths(tmp_path)
    assert ndjson_file in discovered
