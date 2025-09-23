"""Unit tests for macro loading and expansion."""

# === Imports ===
from __future__ import annotations

from pathlib import Path

import pytest

from macro_system.cli import main as cli_main
from macro_system.engine import MacroEngine
from macro_system.macros import load_macros
from macro_system.types import Macro, MacroCycleError, MacroNotFoundError

# === Tests ===


def test_loads_minimum_macro_count():
    path = Path("macro_system/macros.json")
    macros = load_macros(path)
    assert len(macros) >= 80


def test_frontend_macro_expansion_includes_dependencies():
    engine = MacroEngine.from_json(Path("macro_system/macros.json"))
    expansion = engine.expand("::frontendgen")
    assert "Generates a full front-end scaffold" in expansion
    assert "Designs grid layouts" in expansion
    assert "Generates front-end unit tests" in expansion


def test_missing_macro_reference_raises():
    macros = {
        "::root": Macro(name="::root", expansion="root", calls=["::missing"])
    }
    engine = MacroEngine(macros)
    with pytest.raises(MacroNotFoundError):
        engine.expand("::root")


def test_cycle_detection_reports_cycle():
    macros = {
        "::a": Macro(name="::a", expansion="A", calls=["::b"]),
        "::b": Macro(name="::b", expansion="B", calls=["::a"]),
    }
    engine = MacroEngine(macros)
    with pytest.raises(MacroCycleError):
        engine.expand("::a")


def test_available_macros_sorted_listing():
    engine = MacroEngine.from_json(Path("macro_system/macros.json"))
    macros = engine.available_macros()
    assert macros == sorted(macros)
    assert "::frontendgen" in macros


def test_dependency_introspection_recurses_transitively():
    engine = MacroEngine.from_json(Path("macro_system/macros.json"))
    deps = engine.dependencies("::frontendsuite")
    # Should include direct macros and nested children from ::frontendgen
    assert "::frontendgen" in deps
    assert "::frontendgen-tests" in deps


def test_validate_detects_missing_reference():
    macros = {
        "::a": Macro(name="::a", expansion="A", calls=["::missing"]),
        "::b": Macro(name="::b", expansion="B", calls=[]),
    }
    engine = MacroEngine(macros)
    with pytest.raises(MacroNotFoundError):
        engine.validate()


def test_cli_plan_command_outputs_outline(capsys):
    exit_code = cli_main(["--plan", "::frontendgen"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "::frontendgen" in captured.out
    assert "::frontendgen-tests" in captured.out
