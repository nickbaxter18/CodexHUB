"""Unit tests for macro loading and expansion."""

# === Imports ===
from __future__ import annotations

import json
from pathlib import Path

import pytest

from macro_system.cli import main as cli_main
from macro_system.engine import MacroEngine
from macro_system.macros import load_macros
from macro_system.reports import generate_macro_review
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


def test_macro_metadata_is_loaded():
    macros = load_macros(Path("macro_system/macros.json"))
    frontend = macros["::frontendgen"]
    assert frontend.owner_agent == "Frontend Agent"
    assert "Outputs are structured" in frontend.outcomes[1]
    assert "QA Agent MD" in frontend.acceptance_criteria[1]
    assert "qa::review" in frontend.qa_hooks
    assert frontend.phase == "build"
    assert frontend.priority == "P1"
    assert frontend.status == "planned"
    assert frontend.estimated_duration == "8h"
    assert "scaffold" in frontend.tags
    assert frontend.version == "1.1.0"


def test_missing_macro_reference_raises():
    macros = {"::root": Macro(name="::root", expansion="root", calls=["::missing"])}
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
    assert "::frontendgen [Frontend Agent] <P1> (planned)" in captured.out
    assert "::frontendgen-tests" in captured.out


def test_cli_exports_qa_checklist(capsys):
    exit_code = cli_main(["--qa-checklist", "::frontendgen"])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert any(item["macro"] == "::frontendgen-tests" for item in payload)
    root_entry = next(item for item in payload if item["macro"] == "::frontendgen")
    assert root_entry["priority"] == "P1"
    assert root_entry["status"] == "planned"


def test_cli_exports_meta_manifest(capsys):
    exit_code = cli_main(["--meta-manifest", "::frontendgen"])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["root"] == "::frontendgen"
    tests_entry = next(item for item in payload["tasks"] if item["macro"] == "::frontendgen-tests")
    assert tests_entry["dependsOn"] == ["::frontendgen"]
    root_task = next(item for item in payload["tasks"] if item["macro"] == "::frontendgen")
    assert root_task["priority"] == "P1"
    assert root_task["status"] == "planned"


def test_cli_report_outputs_review(capsys):
    exit_code = cli_main(["--report"])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["totalMacros"] >= 80
    assert "agentCoverage" in payload
    assert "recommendations" in payload


def test_generate_macro_review_detects_gaps():
    macros = {
        "::a": Macro(name="::a", expansion="A", calls=[], owner_agent=None),
        "::b": Macro(
            name="::b",
            expansion="B",
            calls=[],
            owner_agent="Frontend Agent",
            outcomes=[
                "Frontend Agent delivers the ::b macro with actionable guidance.",
                "Outputs are structured for downstream agent consumption.",
            ],
            acceptance_criteria=[],
            qa_hooks=[],
        ),
    }

    review = generate_macro_review(macros)

    assert review.coverage.total_macros == 2
    assert review.gaps.unassigned == ["::a"]
    assert review.gaps.missing_acceptance == ["::a", "::b"]
    assert review.gaps.missing_qa_hooks == ["::a", "::b"]
    assert review.gaps.default_outcomes == ["::b"]
    assert review.recommendations  # ensure at least one action exists


def test_cli_exports_schema(capsys):
    exit_code = cli_main(["--export-schema"])
    assert exit_code == 0
    captured = capsys.readouterr()
    schema = json.loads(captured.out)
    assert schema["$schema"].startswith("https://json-schema.org")
    assert "patternProperties" in schema


def test_engine_cache_and_listeners():
    engine = MacroEngine.from_json(Path("macro_system/macros.json"))
    engine.invalidate_cache()
    assert engine.cache_size() == 0

    events: list[str] = []

    def _listener(name: str, expansion: str) -> None:
        events.append(name)

    engine.register_listener(_listener)
    engine.expand("::frontendsuite")

    assert "::frontendsuite" in events
    cached_size = engine.cache_size()
    assert cached_size >= 1

    events.clear()
    engine.expand("::frontendsuite")
    assert events == []  # expansion served from cache
    assert engine.cache_size() == cached_size

    engine.invalidate_cache()
    assert engine.cache_size() == 0


def test_frontendsuite_calls_are_deduplicated():
    macros = load_macros(Path("macro_system/macros.json"))
    frontendsuite = macros["::frontendsuite"]
    assert frontendsuite.calls == ["::frontendgen", "::qa-agent-md-integration"]


def test_fullstacksuite_includes_integration_suite():
    macros = load_macros(Path("macro_system/macros.json"))
    fullstack = macros["::fullstacksuite"]
    assert "::agent-integration-suite" in fullstack.calls
