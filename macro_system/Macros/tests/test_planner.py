"""Header & Purpose: planner-focused regression tests for macro workflows."""

from __future__ import annotations

# === Imports / Dependencies ===
import json
from pathlib import Path

from macro_system.engine import MacroEngine
from macro_system.planner import MacroPlanner

# === Types / Interfaces / Schemas ===
# Tests operate on the ``MacroPlanner`` abstraction.


# === Core Logic / Implementation ===
def build_planner() -> MacroPlanner:
    engine = MacroEngine.from_json(Path("macro_system/Macros/macros.json"))
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

    assert "- ::frontendsuite" in outline
    assert "  - ::frontendgen" in outline
    assert "    - ::frontendgen-tests" in outline


def test_markdown_json_and_task_rendering():
    planner = build_planner()
    markdown = planner.render_markdown("::datasuite")
    assert markdown.startswith("## ::datasuite")
    assert "### ::mockdata" in markdown

    json_payload = planner.render_json("::datasuite")
    payload = json.loads(json_payload)
    assert payload["macro"] == "::datasuite"

    tasks = planner.tasks("::datasuite")
    assert any(task.startswith("::mockdata-sample") for task in tasks)


def test_plan_flatten_preserves_preorder():
    planner = build_planner()
    plan = planner.build("::frontendsuite")
    ordered = plan.flatten()
    assert ordered[0].macro == "::frontendsuite"
    assert any(step.macro == "::frontendgen-tests" for step in ordered)


# === Error & Edge Handling ===
# Planner relies on the engine to surface cycle detection via exceptions.


# === Performance Considerations ===
# Planner fixture reuses a shared engine instance to minimise file I/O.
