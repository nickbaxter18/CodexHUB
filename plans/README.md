# CodexBridge Plan Inbox

CodexBridge ingests AI-authored plan files from `plans/from_gpt/`. The watcher validates
these JSON documents against `codexbridge/schemas/plan.schema.json` and either processes them
or reroutes them for human attention.

- `from_gpt/` — raw plans exported by GPT planners. The watcher removes files from this
  directory once processed.
- `processed/` — successfully executed plans with appended audit metadata.
- `rejected/` — plans that failed validation or require manual review.

Store one plan per JSON file. Filenames should include a timestamp (ISO 8601) and macro name
for traceability, for example `2025-09-23T140001Z__frontend_dashboard.json`.
