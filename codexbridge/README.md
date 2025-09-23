# CodexBridge Foundation

CodexBridge converts high-level GPT planning artefacts into auditable TypeScript macros.
This package now includes the schema, validation utilities, and the automated watcher that
turns approved plans into macro scaffolds.

## Components

- **Schema** — `schemas/plan.schema.json` codifies the contract between GPT planners and the
  local Codex agent.
- **Validator** — `src/plan-validator.js` loads the schema, validates incoming plans, and exposes
  helper methods to guard automation based on safety flags.
- **Watcher** — `src/plan-watcher.js` ingests plans from `plans/from_gpt/`, enforces safety
  policies, scaffolds macros in `macros/`, updates `macros/registry.json`, runs tests, and emits
  audit artefacts (`plans/processed/`, `plans/rejected/`, `results/`, and caches under `cache/`).
- **Types** — `../macros/types.ts` centralises the `MacroContext` contract consumed by generated
  TypeScript macros.

## Usage

Run the watcher once to process any queued plans:

```bash
node codexbridge/src/plan-watcher.js
```

Successful runs move plans to `plans/processed/` and append metadata. Plans that fail validation,
trigger manual-review flags, or experience test failures are moved to `plans/rejected/` with
explanatory diagnostics. The watcher writes execution summaries to `results/` so the GPT planner
can adapt subsequent plans.

## Next Steps

- Expand macro generation to support composition/dependency graphs.
- Integrate the watcher into CI so every pull request validates new plans and macros.
- Extend planner feedback loops with richer analytics derived from the caches.
