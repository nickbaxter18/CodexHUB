"""Unit tests verifying specialist agent behaviour and knowledge retrieval pipelines."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pytest

from agents import (
    AgentTask,
    ArchitectAgent,
    BackendAgent,
    FrontendAgent,
    KnowledgeAgent,
    KnowledgeDocument,
)
from macro_system.engine import MacroEngine
from qa.qa_engine import QAEngine
from qa.qa_event_bus import QAEventBus


@pytest.fixture(scope="module")
def qa_engine() -> QAEngine:
    """Load the canonical QA rules for specialist agent validation."""

    config_dir = Path("config")
    return QAEngine.from_files(config_dir / "qa_rules.json", config_dir / "qa_rules.schema.json")


@pytest.fixture(scope="module")
def macro_engine() -> MacroEngine:
    """Provide a macro engine for expanding specialist agent macros."""

    return MacroEngine.from_json(Path("macro_system/macros.json"))


@pytest.fixture()
def event_bus() -> QAEventBus:
    """Create a fresh event bus per test to avoid cross-test subscriber leakage."""

    return QAEventBus()


def test_frontend_agent_expands_requested_macros(
    qa_engine: QAEngine, macro_engine: MacroEngine, event_bus: QAEventBus
) -> None:
    """Frontend agent should expand explicit macro requests and expose component guidance."""

    agent = FrontendAgent(qa_engine, event_bus, macro_engine=macro_engine)
    task = {"action": "scaffold_interface", "payload": {"macros": ["::frontendgen-layout"]}}
    result = agent.perform_task(task)
    components = result["outputs"]["components"]
    assert "::frontendgen-layout" in components
    assert result["metrics"]["frontend_macros"] == 1
    assert components["::frontendgen-layout"].strip()


def test_backend_agent_supports_custom_handlers(qa_engine: QAEngine, event_bus: QAEventBus) -> None:
    """Backend agent should allow registering bespoke handlers for domain specific actions."""

    agent = BackendAgent(qa_engine, event_bus, macro_engine=None)

    def catalogue_services(task: AgentTask) -> Dict[str, object]:
        services: List[str] = sorted(str(item) for item in task.payload.get("services", []))
        return {"metrics": {"services_indexed": len(services)}, "outputs": {"services": services}}

    agent.register_handler("catalogue", catalogue_services)
    result = agent.perform_task(
        {"action": "catalogue", "payload": {"services": ["billing", "user"]}}
    )
    assert result["metrics"]["services_indexed"] == 2
    assert result["outputs"]["services"] == ["billing", "user"]


def test_architect_agent_generates_blueprint_outline(
    qa_engine: QAEngine, macro_engine: MacroEngine, event_bus: QAEventBus
) -> None:
    """Architect agent should assemble blueprint text using its domain macros."""

    agent = ArchitectAgent(qa_engine, event_bus, macro_engine=macro_engine)
    result = agent.perform_task({"action": "generate_blueprint", "payload": {"limit": 3}})
    blueprint_text = result["outputs"]["blueprint"]
    assert result["metrics"]["architecture_macros"] == 3
    assert len(blueprint_text) > 0


def test_knowledge_agent_returns_ranked_results(qa_engine: QAEngine, event_bus: QAEventBus) -> None:
    """Knowledge agent should retrieve governance answers ranked by simple relevance scoring."""

    documents = [
        KnowledgeDocument(
            identifier="governance-1",
            title="Trust Threshold Guidance",
            content="Trust thresholds determine arbitration priority and drift detection triggers.",
            tags=("governance", "trust"),
        ),
        KnowledgeDocument(
            identifier="governance-2",
            title="Drift Review Playbook",
            content="Drift detection requires manual approval when trust decay exceeds limits.",
            tags=("governance", "drift"),
        ),
    ]
    agent = KnowledgeAgent(qa_engine, event_bus, documents=documents)
    result = agent.perform_task(
        {"action": "query", "payload": {"query": "trust thresholds", "limit": 2}}
    )
    answers = result["outputs"]["answers"]
    assert answers, "Expected the knowledge agent to surface at least one answer"
    assert answers[0]["id"] == "governance-1"
    assert result["metrics"]["results_returned"] == len(answers)
