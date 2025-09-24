"""Unit tests for the KnowledgeAgent retrieval workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pytest

from agents.knowledge_agent import KnowledgeAgent
from qa.qa_engine import QAEngine, QARules
from qa.qa_event_bus import QAEventBus


@pytest.fixture()
def qa_engine_obj() -> QAEngine:
    """Load the QA engine with the repository's rule set."""

    base = Path(__file__).resolve().parents[2]
    rules = QARules.load_from_file(
        base / "config" / "qa_rules.json", base / "config" / "qa_rules.schema.json"
    )
    return QAEngine(rules)


@pytest.fixture()
def knowledge_source(tmp_path: Path) -> Path:
    """Create a temporary NDJSON knowledge source for tests."""

    records: List[Dict[str, object]] = [
        {
            "doc_id": "doc-1",
            "title": "Governance architecture",
            "text": "Codex governance covers fairness, privacy, and QA automation.",
            "tags": ["governance", "qa"],
        },
        {
            "doc_id": "doc-2",
            "title": "Brain Block: mobile approvals",
            "text": "Mobile orchestration enables approvals on-device for Codex workflows.",
            "tags": ["mobile", "approvals"],
        },
    ]
    path = tmp_path / "brain.ndjson"
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
    return path


def test_knowledge_agent_returns_results(qa_engine_obj: QAEngine, knowledge_source: Path) -> None:
    """A well-formed query should yield QA-approved results."""

    bus = QAEventBus()
    agent = KnowledgeAgent("Knowledge", qa_engine_obj, bus, [knowledge_source])
    result = agent.run_with_qa("governance QA policies")

    assert result["results_found"] >= 1
    assert result["coverage_ratio"] > 0
    assert result["qa_evaluation"].passed is True
    assert result["qa_tests_executed"] == qa_engine_obj.get_agent_tests("Knowledge")


def test_knowledge_agent_tag_filtering(qa_engine_obj: QAEngine, knowledge_source: Path) -> None:
    """Tag constraints should restrict the result set."""

    bus = QAEventBus()
    agent = KnowledgeAgent("Knowledge", qa_engine_obj, bus, [knowledge_source])
    result = agent.run_with_qa("approvals", require_tags=["mobile"])

    assert result["results_found"] == 1
    assert all("mobile" in res["tags"] for res in result["results"])


def test_knowledge_agent_flags_missing_results(
    qa_engine_obj: QAEngine, knowledge_source: Path
) -> None:
    """Queries with no hits should trigger metric violations via QA."""

    bus = QAEventBus()
    agent = KnowledgeAgent("Knowledge", qa_engine_obj, bus, [knowledge_source])
    result = agent.run_with_qa("nonexistent topic")

    assert result["results_found"] == 0
    assert result["qa_evaluation"].passed is False
    violations = {violation["metric"] for violation in result["qa_metric_violations"]}
    assert "results_found" in violations
