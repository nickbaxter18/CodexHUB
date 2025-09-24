"""Tests for actionable planning derived from macros."""

# === Imports ===
from __future__ import annotations

from pathlib import Path

from macro_system.engine import MacroEngine
from macro_system.planner import MacroPlanner

# === Tests ===


def build_planner() -> MacroPlanner:
    engine = MacroEngine.from_json(Path("macro_system/macros.json"))
    return MacroPlanner(engine)


def test_planner_builds_hierarchical_structure():
    planner = build_planner()
    plan = planner.build("::frontendgen")

    assert plan.macro == "::frontendgen"
    child_names = {child.macro for child in plan.children}
    assert "::frontendgen-layout" in child_names
    assert "::frontendgen-tests" in child_names
    # leaf tasks should correspond to macros without further calls
    leaf_macros = {leaf.macro for leaf in plan.leaf_tasks()}
    assert "::frontendgen-docs" in leaf_macros
    assert "::frontendgen-motion" in leaf_macros


def test_outline_contains_nested_steps():
    planner = build_planner()
    outline = planner.render_outline("::frontendsuite")

    assert "- ::frontendsuite [QA Agent] <P0> (ready)" in outline
    assert "  - ::frontendgen [Frontend Agent] <P1> (planned)" in outline
    assert "    - ::frontendgen-tests [QA Agent]" in outline


def test_plan_dict_contains_metadata():
    planner = build_planner()
    plan = planner.build("::frontendgen")
    serialised = plan.to_dict()

    assert serialised["ownerAgent"] == "Frontend Agent"
    assert "Outputs are structured" in serialised["outcomes"][1]
    assert serialised["children"][0]["ownerAgent"] == "Frontend Agent"
    assert serialised["priority"] == "P1"
    assert serialised["phase"] == "build"
    assert serialised["estimatedDuration"] == "8h"
    assert "scaffold" in serialised["tags"]
    assert serialised["children"][0]["priority"] is None


def test_plan_exports_checklist_and_manifest():
    planner = build_planner()
    plan = planner.build("::frontendgen")

    checklist = plan.to_qa_checklist()
    assert any(item["macro"] == "::frontendgen" for item in checklist)
    assert any(item["macro"] == "::frontendgen-tests" for item in checklist)

    manifest = plan.to_manifest()
    assert manifest["root"] == "::frontendgen"
    root_task = next(item for item in manifest["tasks"] if item["macro"] == "::frontendgen")
    assert root_task["dependsOn"] == []
    assert root_task["priority"] == "P1"
    assert root_task["phase"] == "build"
    child_task = next(item for item in manifest["tasks"] if item["macro"] == "::frontendgen-tests")
    assert child_task["dependsOn"] == ["::frontendgen"]
    assert child_task["priority"] is None
