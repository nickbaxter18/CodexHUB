"""Integration smoke tests for global system initializers."""

from agents.specialist_agents import KnowledgeAgent as SpecialistKnowledgeAgent
from qa.qa_engine import QAEngine, QARules
from src.knowledge import auto_loader as knowledge_auto_loader, brain_blocks_integration
from src.mobile import mobile_app


def test_get_auto_loader_initializes_singleton() -> None:
    """Factory should return a configured knowledge auto-loader with QA plumbing."""

    knowledge_auto_loader._global_auto_loader = None
    loader = knowledge_auto_loader.get_auto_loader()
    try:
        assert isinstance(loader.knowledge_agent, SpecialistKnowledgeAgent)
        assert isinstance(loader.knowledge_agent.qa_engine, QAEngine)
        assert isinstance(loader.knowledge_agent.qa_engine.rules, QARules)
    finally:
        knowledge_auto_loader._global_auto_loader = None


def test_get_brain_blocks_integration_initializes_singleton() -> None:
    """Factory should construct a brain blocks integration backed by KnowledgeAgent."""

    brain_blocks_integration._global_brain_blocks = None
    integration = brain_blocks_integration.get_brain_blocks_integration()
    try:
        assert isinstance(integration.knowledge_agent, SpecialistKnowledgeAgent)
        assert isinstance(integration.knowledge_agent.qa_engine, QAEngine)
        assert isinstance(integration.knowledge_agent.qa_engine.rules, QARules)
    finally:
        brain_blocks_integration._global_brain_blocks = None


def test_get_mobile_app_initializes_singleton() -> None:
    """Factory should return a mobile app wired with QA engine defaults."""

    mobile_app._global_mobile_app = None
    app = mobile_app.get_mobile_app()
    try:
        assert app.control_interface.qa_engine.rules.version == "1.0"
        assert isinstance(app.control_interface.qa_engine, QAEngine)
        assert isinstance(app.control_interface.qa_engine.rules, QARules)
    finally:
        mobile_app._global_mobile_app = None
