# Macro System for AI Prompt Generation

## Overview

The Macro System for AI Prompt Generation provides a modular way to turn concise
macro invocations (for example `::frontendgen`) into fully fledged sets of
instructions for building production-grade software. Each macro can expand into
text as well as invoke additional macros, allowing complex scaffolds to be
assembled from small reusable building blocks.

## Features

- Pure JSON storage for macro definitions to guarantee auditability.
- Recursive expansion with cycle detection and helpful diagnostics.
- Structured agent metadata (owners, outcomes, acceptance criteria, QA hooks,
  phases, priorities and durations) on every macro to support orchestration
  with QA and Meta agents.
- Built-in metadata audits plus CLI exports for QA checklists and Meta Agent
  orchestration manifests.
- Persistent expansion cache with optional listener hooks so automation can
  react to newly computed expansions without recomputation overhead.
- JSON Schema utilities for validating catalogues and sharing contracts with
  partner tools.
- Support for hierarchical macros covering front-end, back-end, testing,
  security, deployment, analytics and more.
- Extensible design that allows adding or modifying macros solely by editing
  `macros.json`—no code changes required.

## Usage

```python
from macro_system import MacroEngine

engine = MacroEngine.from_json("macros.json")
engine.validate()  # Optional integrity check
print(engine.expand("::masterdev"))
```

### Introspection Helpers

The engine now exposes convenience utilities for advanced tooling:

- `available_macros()` – returns a sorted list of macro names for discovery.
- `describe(name)` – returns the underlying `Macro` dataclass for inspection.
- `dependencies(name, recursive=True)` – explores macro call chains.
- `expand_many(["::frontendgen", "::backendgen"])` – expands several macros
  at once while sharing memoized results.
- `validate()` – verifies the entire macro catalogue for missing references or
  cycles without performing full expansion.

These helpers make it straightforward to embed the macro system into custom
developer tooling, dashboards or prompt authoring assistants.

### Command-Line Interface

A lightweight CLI is provided for rapid experimentation:

```bash
python -m macro_system.cli --list
python -m macro_system.cli --describe ::frontendgen
python -m macro_system.cli --deps ::masterdev
python -m macro_system.cli --validate ::masterdev
python -m macro_system.cli ::frontendsuite ::backendsuite --output plan.txt
python -m macro_system.cli --qa-checklist ::frontendgen > qa.json
python -m macro_system.cli --meta-manifest ::masterdev > manifest.json
python -m macro_system.cli --report
python -m macro_system.cli --export-schema > macro-schema.json
```

The CLI supports listing and describing macros, inspecting dependencies,
validating the graph, exporting combined expansions directly to disk and
rendering nested execution plans for automation. The new checklist/manifest
commands provide QA-ready tasks and orchestrator manifests for downstream
agents, `--report` surfaces metadata gaps across the catalogue and
`--export-schema` publishes the JSON Schema contract for the macro catalogue.

### Schema and Validation

The CLI exports the schema so that QA Agent MD and Meta Agent pipelines can
validate catalogues before execution. The loader enforces the same constraints
at runtime, guaranteeing that keys such as `phase`, `priority`, `status`,
`estimatedDuration` and `tags` remain well-formed across macro definitions.

### Caching & Observability

`MacroEngine` now memoises expansions across calls and exposes listener hooks:

```python
def on_expand(name: str, expansion: str) -> None:
    print("Expanded", name)

engine = MacroEngine.from_json("macros.json")
engine.register_listener(on_expand)
engine.expand("::frontendsuite")  # Listener fires only for uncached macros
```

You can clear the memoised results with `engine.invalidate_cache()` or inspect
the current cache size via `engine.cache_size()` when debugging orchestration
traffic.

### Actionable Plans

For agents that need structured steps rather than plain prose, the
`MacroPlanner` converts macros into hierarchical plans. These plans can be
serialised as outlines or JSON to feed downstream tooling or orchestrators.

```python
from macro_system import MacroEngine, MacroPlanner

engine = MacroEngine.from_json("macros.json")
planner = MacroPlanner(engine)

plan = planner.build("::masterdev")
print(plan.to_outline())  # Human readable
json_payload = plan.to_dict()  # Structured for programmatic consumption
qa_items = plan.to_qa_checklist()  # QA Agent MD checklist payload
manifest = plan.to_manifest()  # Meta Agent orchestration manifest
```

The CLI exposes the same capability:

```bash
python -m macro_system.cli --plan ::masterdev
python -m macro_system.cli --plan-json ::fullstacksuite
```

### Agent Metadata & Migration

Each macro now carries agent-aware metadata. When introducing new macros or
upgrading legacy catalogues, use the migration utility to populate the fields
automatically:

```bash
python -m macro_system.migrations.add_agent_metadata path/to/macros.json
```

The script infers the owning agent, populates default outcomes, and injects QA
hooks so that QA/Meta orchestration tools can consume the catalogue immediately.

## Philosophy

The system is intentionally data-driven. Macro behaviour lives entirely in
`macros.json`, while the Python engine focuses on reliable loading, validation
and expansion. This separation allows teams to evolve their macro catalogue
without redeploying code.

## Project Structure

- `macros.json` – Plain JSON macro definitions.
- `types.py` – Dataclasses and custom exceptions.
- `macros.py` – Loading and validation logic for JSON macros.
- `engine.py` – Recursive macro expansion engine with cycle detection.
- `tests/` – Automated tests covering loading, expansion, error handling and
  cycle detection.

## Testing

Run the unit tests with:

```bash
python -m pytest macro_system/tests
```
