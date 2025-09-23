"""Header & Purpose: regression tests for agent-oriented orchestration."""

from __future__ import annotations

# === Imports / Dependencies ===
from pathlib import Path

from macro_system import MacroEngine, MacroOrchestrator

# === Types / Interfaces / Schemas ===
# Tests leverage the default macro catalogue for realistic scenarios.


# === Core Logic / Implementation ===
CATALOG_PATH = Path("macro_system/Macros/macros.json")


def test_orchestrator_assigns_specialist_agents():
    engine = MacroEngine.from_json(CATALOG_PATH)
    orchestrator = MacroOrchestrator(engine)

    assignments = orchestrator.assign("::fullstacksuite")
    mapping = {assignment.agent: assignment.macros() for assignment in assignments}

    assert "Frontend Agent" in mapping
    assert any(name.startswith("::frontend") for name in mapping["Frontend Agent"])

    assert "Backend Agent" in mapping
    backend_macros = mapping["Backend Agent"]
    assert any(name.startswith("::backend") for name in backend_macros)
    assert any(name.startswith("::dbdesign") for name in backend_macros)

    assert "CI/CD Agent" in mapping
    cicd_macros = mapping["CI/CD Agent"]
    assert any(name.startswith("::cicd") for name in cicd_macros)
    assert any(name.startswith("::deploy") for name in cicd_macros)


def test_orchestrator_respects_overrides_and_includes_parents():
    engine = MacroEngine.from_json(CATALOG_PATH)
    orchestrator = MacroOrchestrator(engine, agent_map={"frontend": "Design Agent"})

    assignments = orchestrator.assign("::frontendsuite", include_non_leaf=True)
    agents = {assignment.agent for assignment in assignments}
    assert "Design Agent" in agents

    macros = {macro for assignment in assignments for macro in assignment.macros()}
    assert "::frontendsuite" in macros

    payload = assignments[0].to_dict()
    assert payload["agent"]
    assert payload["steps"]
    assert payload["instructions_text"]


def test_orchestrator_assign_many_combines_results():
    engine = MacroEngine.from_json(CATALOG_PATH)
    orchestrator = MacroOrchestrator(engine)

    assignments = orchestrator.assign_many(["::frontendsuite", "::backendsuite"])
    mapping = {assignment.agent: assignment.macros() for assignment in assignments}

    assert "Frontend Agent" in mapping
    assert any(name.startswith("::frontend") for name in mapping["Frontend Agent"])

    assert "Backend Agent" in mapping
    assert any(name.startswith("::backend") for name in mapping["Backend Agent"])


def test_orchestrator_dispatch_formats_prompts_and_outlines():
    engine = MacroEngine.from_json(CATALOG_PATH)
    orchestrator = MacroOrchestrator(engine)

    prompts = orchestrator.dispatch(["::frontendsuite", "::datasuite"], format="prompt")
    assert "Frontend Agent" in prompts
    assert prompts["Frontend Agent"].startswith("You are Frontend Agent")
    assert "::frontendgen" in prompts["Frontend Agent"]

    outlines = orchestrator.dispatch("::frontendsuite", format="outline")
    assert outlines["Frontend Agent"].startswith("## Frontend Agent")

    instructions = orchestrator.dispatch("::backendsuite", format="text")
    assert "Scaffolds CRUD endpoints" in instructions["Backend Agent"]


# === Error & Edge Handling ===
# Defaults ensure missing metadata falls back to the Meta Agent; tests cover
# overrides and combined macro execution to validate behaviour.


# === Performance Considerations ===
# Orchestrator reuses cached planner results implicitly; tests focus on
# functional correctness rather than benchmarks.
