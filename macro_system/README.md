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
```

The CLI supports listing and describing macros, inspecting dependencies,
validating the graph, exporting combined expansions directly to disk and
rendering nested execution plans for automation.

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
```

The CLI exposes the same capability:

```bash
python -m macro_system.cli --plan ::masterdev
python -m macro_system.cli --plan-json ::fullstacksuite
```

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

