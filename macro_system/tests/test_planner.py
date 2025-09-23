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

    assert "- ::frontendsuite" in outline
    assert "  - ::frontendgen" in outline
    assert "    - ::frontendgen-tests" in outline
