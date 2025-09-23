# Macros Package

## Overview
The Macros package provides a modular way to turn concise macro invocations
(for example `::frontendgen`) into fully fledged sets of instructions for
building production-grade software. Each macro can expand into text as well as
invoke additional macros, allowing complex scaffolds to be assembled from small
reusable building blocks.

## Key Capabilities
- Pure JSON storage for macro definitions to guarantee auditability.
- Recursive expansion with cycle detection, validation, strict auditing, and
  traversal traces.
- Memoised caching that can be inspected or cleared to accelerate repeated
  expansions.
- Catalogue analytics (roots, leaves, depth, branching factor) and structured
  audit reports (missing references, cycles, unreachable macros).
- Metadata tagging, filtering, and grouping for rapid macro discovery across
  domains, pillars, and execution levels.
- Hierarchical plans that render as outlines, Markdown documents, JSON payloads,
  or flattened task lists.
- Advanced CLI helpers for searching macros, exporting plans, listing tasks,
  viewing traversal traces, running audits, explaining dependency paths, and
  enumerating ancestor relationships.
- Agent-oriented orchestration that groups plan steps by specialist roles for
  multi-agent collaboration workflows.
- Repository utilities for merging custom catalogues, reloading sources, and
  exporting consolidated snapshots for audit trails.

## Usage
```python
from macro_system import MacroEngine

engine = MacroEngine.from_json("macro_system/Macros/macros.json")
engine.validate()  # Optional integrity check
print(engine.expand("::masterdev"))
```

### Advanced Introspection
The engine exposes convenience utilities for sophisticated tooling:

- `available_macros()` – discover macros alphabetically.
- `describe(name)` – inspect the underlying `Macro` dataclass (including
  metadata).
- `dependencies(name, recursive=True)` – explore macro call chains.
- `ancestors(name, recursive=True)` – list macros that depend on the given
  macro.
- `expand_many([...], use_cache=True)` – expand several macros while reusing
  cached results.
- `expand_with_trace(name)` – capture the traversal order alongside the
  expansion result.
- `search(query)` – find macros by name or expansion text.
- `filter_by_metadata({"domain": "frontend"})` – return macros with matching
  metadata.
- `group_by_metadata("domain")` – cluster macros by metadata values for
  reporting or dashboards.
- `render(name, context)` – substitute `{{placeholders}}` using context
  mappings for project-aware output.
- `placeholders(name, recursive=True)` – list the placeholder tokens required by
  a macro and optionally its dependencies.
- `audit(entrypoints=None)` – produce a `MacroAudit` detailing undefined
  references, cycles, unreachable macros, and statistics.
- `validate_strict(entrypoints=None)` – raise on audit findings to enforce clean
  catalogues.
- `stats()` – return aggregated catalogue metrics via the `MacroStats` dataclass.
- `clear_cache()` / `cache_info()` – manage memoised expansions.
- `explain_path(source, target)` – report a dependency path between two macros.

These helpers make it straightforward to embed the macro system into custom
developer tooling, dashboards, or prompt authoring assistants.

### Planning Utilities
For agents that need structured steps rather than plain prose, the
`MacroPlanner` converts macros into hierarchical plans. Plans support outline,
Markdown, dictionary, and flattened task renderings:

```python
from macro_system import MacroEngine, MacroPlanner

engine = MacroEngine.from_json("macro_system/Macros/macros.json")
planner = MacroPlanner(engine)

plan = planner.build("::masterdev")
print(plan.to_outline())        # Human-readable outline
print(plan.to_markdown())       # Markdown document
print(plan.to_dict())           # Structured for programmatic consumption
print(planner.tasks("::masterdev"))  # Leaf task summaries
```

### Agent-Oriented Orchestration
Coordinate execution responsibilities across the U-DIG IT agent roster using the
`MacroOrchestrator`. Tasks are automatically allocated using macro metadata, and
domain-to-agent mappings can be customised when needed:

```python
from macro_system import MacroEngine, MacroOrchestrator

engine = MacroEngine.from_json("macro_system/Macros/macros.json")
orchestrator = MacroOrchestrator(engine)

assignments = orchestrator.assign("::fullstacksuite")
for assignment in assignments:
    print(assignment.to_outline())
```

Override role mappings or combine multiple macros by calling
`orchestrator.assign_many([...], include_non_leaf=True)`. Each
`AgentAssignment` exposes helper methods for outlines, JSON-friendly dicts,
conversational prompts, and raw instruction text, making it straightforward to
feed agent-specific payloads into automation workflows.

```python
assignment.to_outline()        # Markdown brief for QA or design reviews
assignment.instructions_text() # Concise bullet list for agent execution
assignment.to_prompt()         # Conversational prompt packaged for LLM agents
assignment.to_dict()           # JSON payload for downstream automation
```

CLI equivalents are available for rapid experimentation:

```bash
python -m macro_system.cli --assign-agents ::masterdev
python -m macro_system.cli --assign-json ::frontendsuite --agent-map frontend="Design Agent"
python -m macro_system.cli --assign-agents ::frontendsuite --assign-include-non-leaf
python -m macro_system.cli --assign-prompts ::masterdev
python -m macro_system.cli --assign-prompts-format outline --assign-prompts ::frontendsuite ::datasuite
```

### Catalogue Management
Combine the bundled catalogue with organisation-specific JSON files using the
`MacroRepository` or the CLI:

```python
from pathlib import Path

from macro_system import MacroEngine, MacroRepository

repository = MacroRepository([
    Path("macro_system/Macros/macros.json"),
    Path("~/team-catalog.json").expanduser(),
])
engine = repository.engine()
print(engine.expand("::custom-suite"))

repository.export(Path("merged-catalog.json"))  # Snapshot the merged view
```

Command-line equivalents:

```bash
python -m macro_system.cli --catalog ~/team-catalog.json --list-sources
python -m macro_system.cli --catalog-dir ./catalogs --export-merged merged.json
python -m macro_system.cli --no-default --catalog custom.json --list
```

### Contextual Rendering
The engine also supports templated placeholders. Call
`engine.render("::project-kickoff", {"project_name": "Atlas"})` to tailor
expansions and run `engine.placeholders("::project-kickoff")` to discover the
expected context keys. The CLI mirrors these capabilities through the
`--context`, `--context-file`, `--allow-partial`, and `--placeholders` flags for
fully automated workflows.

### Command-Line Interface
The enhanced CLI supports rapid experimentation and automation:

```bash
python -m macro_system.cli --list
python -m macro_system.cli --search frontend
python -m macro_system.cli --filter-meta domain=frontend
python -m macro_system.cli --group-meta domain
python -m macro_system.cli --stats
python -m macro_system.cli --audit --entrypoint ::masterdev
python -m macro_system.cli --describe ::frontendgen
python -m macro_system.cli --deps ::masterdev
python -m macro_system.cli --ancestors ::frontendgen
python -m macro_system.cli --plan ::frontendsuite
python -m macro_system.cli --plan-json ::fullstacksuite
python -m macro_system.cli --markdown ::masterdev
python -m macro_system.cli --tasks ::masterdev
python -m macro_system.cli --trace ::datasuite
python -m macro_system.cli --path ::masterdev ::frontendgen
python -m macro_system.cli --catalog extra.json --list-sources
python -m macro_system.cli --catalog-dir ./catalogs --export-merged merged.json
python -m macro_system.cli ::frontendsuite ::backendsuite --output plan.txt
```

### Folder Layout
All macro functionality now lives inside the `macro_system/Macros` directory:

- `macros.json` – Plain JSON macro definitions.
- `catalog.py` – Loading, validation, metadata parsing, and catalogue merging
  utilities.
- `engine.py` – Recursive macro expansion engine with caching and analytics.
- `repository.py` – Repository for merging catalogues, refreshing sources, and
  exporting merged JSON snapshots.
- `planner.py` – Hierarchical plan construction helpers.
- `types.py` – Dataclasses, exceptions, audits, and statistics utilities.
- `cli.py` – Command-line tooling for expansion, planning, auditing, and graph
  exploration.
- `tests/` – Automated tests covering loading, expansion, planning, analytics,
  and CLI behaviour.

## Testing
Run the unit tests with:

```bash
python -m pytest macro_system/Macros/tests
```
