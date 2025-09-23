"""Header & Purpose: integration tests for macro engine, planner, and CLI."""

from __future__ import annotations

# === Imports / Dependencies ===
import json
from pathlib import Path

import pytest

from macro_system.cli import main as cli_main
from macro_system.engine import MacroEngine
from macro_system.macros import load_catalogs, load_default_catalog, load_macros
from macro_system.types import (
    Macro,
    MacroCycleError,
    MacroNotFoundError,
    MacroRenderError,
    MacroValidationError,
)

# === Types / Interfaces / Schemas ===
# Tests manipulate :class:`Macro` dataclasses for targeted scenarios.


# === Core Logic / Implementation ===
CATALOG_PATH = Path("macro_system/Macros/macros.json")


def test_loads_minimum_macro_count():
    macros = load_macros(CATALOG_PATH)
    assert len(macros) >= 80


def test_load_macros_supports_metadata_and_merge():
    catalog_a = {
        "::root": {
            "expansion": "root",
            "calls": ["::child"],
            "metadata": {"domain": "test"},
        },
        "::child": {"expansion": "child", "calls": []},
    }
    catalog_b = {"::extra": {"expansion": "extra", "calls": []}}
    macros = load_macros(catalog_a)
    assert macros["::root"].metadata["domain"] == "test"

    merged = load_catalogs([catalog_a, catalog_b])
    assert "::extra" in merged


def test_frontend_macro_expansion_includes_dependencies():
    engine = MacroEngine.from_json(CATALOG_PATH)
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
    engine = MacroEngine.from_json(CATALOG_PATH)
    macros = engine.available_macros()
    assert macros == sorted(macros)
    assert "::frontendgen" in macros


def test_dependency_and_ancestor_introspection():
    engine = MacroEngine.from_json(CATALOG_PATH)
    deps = engine.dependencies("::frontendsuite")
    assert "::frontendgen" in deps
    assert "::frontendgen-tests" in deps

    parents = engine.ancestors("::frontendgen")
    assert "::frontendsuite" in parents
    assert "::fullstacksuite" in parents


def test_validate_detects_missing_reference():
    macros = {
        "::a": Macro(name="::a", expansion="A", calls=["::missing"]),
        "::b": Macro(name="::b", expansion="B", calls=[]),
    }
    engine = MacroEngine(macros)
    with pytest.raises(MacroNotFoundError):
        engine.validate()


def test_validate_strict_raises_on_unreachable():
    macros = {
        "::root": Macro(name="::root", expansion="root", calls=["::child"]),
        "::child": Macro(name="::child", expansion="child", calls=[]),
        "::orphan": Macro(name="::orphan", expansion="orphan", calls=[]),
    }
    engine = MacroEngine(macros)
    with pytest.raises(MacroValidationError):
        engine.validate_strict(entrypoints=["::root"])


def test_engine_cache_and_trace_behaviour():
    engine = MacroEngine.from_json(CATALOG_PATH)
    engine.clear_cache()
    initial_expansion, trace = engine.expand_with_trace("::frontendgen")
    assert initial_expansion.startswith("Generates a full front-end scaffold")
    assert trace[0] == "::frontendgen"

    _, cached_trace = engine.expand_with_trace("::frontendgen")
    assert cached_trace[0].endswith("(cached)")
    assert engine.cache_info()["cached_macros"] >= 1


def test_render_with_context_and_placeholders():
    macros = {
        "::brief": Macro(
            name="::brief",
            expansion="Focus on {{primary_goal}} outcomes and success metrics.",
            calls=[],
        ),
        "::combo": Macro(
            name="::combo",
            expansion="Launch {{project_name}} initiative with stellar positioning.",
            calls=["::brief"],
        ),
    }
    engine = MacroEngine(macros)
    context = {"project_name": "Atlas", "primary_goal": "automation"}

    rendered = engine.render("::combo", context)
    assert "Atlas" in rendered
    assert "automation" in rendered

    placeholders = engine.placeholders("::combo")
    assert placeholders == ["primary_goal", "project_name"]

    direct_only = engine.placeholders("::combo", recursive=False)
    assert direct_only == ["project_name"]

    with pytest.raises(MacroRenderError):
        engine.render("::combo", {"project_name": "Atlas"})

    partial = engine.render("::combo", {"project_name": "Atlas"}, strict=False)
    assert "{{primary_goal}}" in partial


def test_engine_stats_search_audit_and_path():
    engine = MacroEngine(load_default_catalog())
    stats = engine.stats()
    assert stats.total_macros >= 80
    assert "::masterdev" in stats.root_macros
    assert stats.max_depth >= 2

    matches = engine.search("frontend")
    names = {macro.name for macro in matches}
    assert "::frontendgen" in names

    audit = engine.audit(entrypoints=["::masterdev"])
    assert "::masterdev" in audit.entrypoints
    assert audit.stats.total_macros == stats.total_macros

    path = engine.explain_path("::masterdev", "::frontendgen-tests")
    assert path[0] == "::masterdev"
    assert path[-1] == "::frontendgen-tests"


def test_cli_plan_command_outputs_outline(capsys):
    exit_code = cli_main(["--plan", "::frontendgen"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "::frontendgen" in captured.out
    assert "::frontendgen-tests" in captured.out


def test_cli_audit_and_path_commands(capsys):
    assert cli_main(["--audit"]) == 0
    audit_output = capsys.readouterr().out
    assert "undefined_references" in audit_output


def test_engine_metadata_filter_and_grouping():
    engine = MacroEngine.from_json(CATALOG_PATH)
    frontend_macros = engine.filter_by_metadata({"domain": "frontend"})
    names = {macro.name for macro in frontend_macros}
    assert "::frontendgen" in names
    assert any(name.startswith("::frontendgen-") for name in names)

    grouped = engine.group_by_metadata("domain")
    assert "frontend" in grouped
    assert any(macro.name == "::frontendgen" for macro in grouped["frontend"])


def test_cli_metadata_filtering_and_grouping(capsys):
    exit_code = cli_main(["--filter-meta", "domain=frontend"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "::frontendgen" in output
    assert "::frontendgen-docs" in output

    exit_code = cli_main(["--group-meta", "domain"])
    assert exit_code == 0
    grouped_output = capsys.readouterr().out
    payload = json.loads(grouped_output)
    assert "frontend" in payload
    assert any(name == "::frontendgen" for name in payload["frontend"])


def test_cli_metadata_filter_validation(capsys):
    exit_code = cli_main(["--filter-meta", "invalidpair"])
    assert exit_code == 2
    err = capsys.readouterr().err
    assert "Metadata filters must be provided" in err

    assert cli_main(["--path", "::masterdev", "::frontendgen"]) == 0
    path_output = capsys.readouterr().out.strip()
    assert path_output.startswith("::masterdev")


def test_cli_context_render_and_placeholders(capsys, tmp_path):
    assert cli_main(["--placeholders", "::project-kickoff"]) == 0
    placeholder_output = capsys.readouterr().out.splitlines()
    assert "project_name" in placeholder_output
    assert "primary_goal" in placeholder_output

    exit_code = cli_main(
        [
            "--context",
            "project_name=Atlas",
            "--context",
            "primary_goal=automation",
            "::project-kickoff",
        ]
    )
    assert exit_code == 0
    rendered = capsys.readouterr().out
    assert "Atlas" in rendered
    assert "automation" in rendered

    exit_code = cli_main(["--context", "project_name=Atlas", "::project-kickoff"])
    assert exit_code == 1
    failure = capsys.readouterr()
    assert "Missing values for placeholders" in failure.err

    context_file = tmp_path / "context.json"
    context_file.write_text(
        json.dumps({"project_name": "Nova", "primary_goal": "expansion"}),
        encoding="utf-8",
    )
    exit_code = cli_main(["--context-file", str(context_file), "::project-kickoff"])
    assert exit_code == 0
    rendered_file = capsys.readouterr().out
    assert "Nova" in rendered_file
    assert "expansion" in rendered_file

    exit_code = cli_main(
        ["--context", "project_name=Atlas", "--allow-partial", "::project-kickoff"]
    )
    assert exit_code == 0
    partial = capsys.readouterr().out
    assert "{{primary_goal}}" in partial


def test_cli_assign_agents_outputs_outline(capsys):
    exit_code = cli_main(["--assign-agents", "::frontendsuite"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Frontend Agent" in output
    assert "::frontendgen" in output


def test_cli_assign_agents_json_with_overrides(capsys):
    exit_code = cli_main(
        ["--agent-map", "frontend=Design Agent", "--assign-json", "::frontendsuite"]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert any(entry["agent"] == "Design Agent" for entry in payload)


def test_cli_assign_prompts_outputs_agent_prompts(capsys):
    exit_code = cli_main(["--assign-prompts", "::frontendsuite"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "You are Frontend Agent" in output
    assert "::frontendgen" in output


def test_cli_assign_prompts_respects_format(capsys):
    exit_code = cli_main(
        ["--assign-prompts-format", "outline", "--assign-prompts", "::frontendsuite"]
    )
    assert exit_code == 0
    outline_output = capsys.readouterr().out
    assert "## Frontend Agent" in outline_output

    exit_code = cli_main(
        ["--assign-prompts-format", "text", "--assign-prompts", "::backendsuite"]
    )
    assert exit_code == 0
    text_output = capsys.readouterr().out
    assert "## Backend Agent" in text_output
    assert "Scaffolds CRUD endpoints" in text_output


def test_cli_stats_search_and_strict_validation(capsys):
    assert cli_main(["--stats"]) == 0
    stats_output = capsys.readouterr().out
    assert "total_macros" in stats_output

    assert cli_main(["--search", "frontend"]) == 0
    search_output = capsys.readouterr().out
    assert "::frontendgen" in search_output

    assert cli_main(["--ancestors", "::frontendgen"]) == 0
    ancestor_output = capsys.readouterr().out
    assert "::frontendsuite" in ancestor_output

    assert cli_main(["--validate-strict"]) == 0


def test_cli_catalog_sources_and_export(tmp_path, capsys):
    custom_dir = tmp_path / "catalogs"
    custom_dir.mkdir()
    custom_macro = {
        "::custom": {"expansion": "Custom expansion", "calls": []},
    }
    custom_path = custom_dir / "custom.json"
    custom_path.write_text(json.dumps(custom_macro), encoding="utf-8")

    exit_code = cli_main([
        "--no-default",
        "--catalog-dir",
        str(custom_dir),
        "--list-sources",
    ])
    assert exit_code == 0
    sources_output = capsys.readouterr().out.splitlines()
    assert str(custom_path) in sources_output

    export_path = tmp_path / "merged.json"
    exit_code = cli_main(
        [
            "--no-default",
            "--catalog",
            str(custom_path),
            "--export-merged",
            str(export_path),
        ]
    )
    assert exit_code == 0
    export_summary = json.loads(capsys.readouterr().out)
    assert export_summary["total_macros"] == 1
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert payload["::custom"]["expansion"] == "Custom expansion"


# === Error & Edge Handling ===
# Negative tests ensure exceptions propagate for invalid macro definitions.


# === Performance Considerations ===
# Tests reuse shared catalogue path to avoid redundant JSON loading overhead.
