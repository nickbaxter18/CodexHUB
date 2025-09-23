# CodexBridge File Map

| Path | Purpose |
| ---- | ------- |
| `.codexrc` | Repository-level configuration supplying CodexBridge path/layout overrides, validated against `codexrc.schema.json`. |
| `codexbridge/schemas/codexrc.schema.json` | JSON Schema governing `.codexrc` structure to guarantee deterministic watcher behaviour. |
| `codexbridge/schemas/plan.schema.json` | Canonical JSON Schema describing GPT-authored macro plans. |
| `codexbridge/src/codexrc-loader.js` | Loader that parses `.codexrc`, applies defaults, resolves paths, and surfaces configuration diagnostics. |
| `codexbridge/src/plan-validator.js` | Runtime validator providing schema enforcement, error reporting, and automation guards. |
| `codexbridge/src/plan-watcher.js` | Processes incoming plans, generates macro stubs, updates registries/caches, executes tests, and archives audit artefacts. |
| `macros/types.ts` | Shared TypeScript types consumed by generated macros (e.g. `MacroContext`). |
| `macros/registry.json` | Registry cataloguing generated macros and their governance metadata. |
| `cache/macro_output.json` | Cache storing metadata for generated macros (path, timestamp, status). |
| `cache/test_outcomes.json` | Cache capturing the latest test outcomes keyed by macro identifier. |
| `plans/from_gpt/` | Inboxes used by the watcher to receive plans from GPT planners. |
| `plans/processed/` | Archive of processed plans augmented with macro/test metadata for auditing. |
| `plans/rejected/` | Plans that failed validation or require manual review. |
| `results/` | Feedback artefacts summarising watcher execution for planner introspection. |
