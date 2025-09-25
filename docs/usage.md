# Usage Guide

This document captures the most common workflows for working with CodexHUB once your environment is configured.

## Running the Express scaffolding

```bash
pnpm run dev
```

- Serves the default Express app on `http://localhost:4000`.
- Exposes `/health` for smoke testing.
- Extend `src/index.js` with additional routes or mount API routers from `backend/` as needed.

## Editor health-test utilities

The editor helper lives under `backend/health-test.js` and requires an `EDITOR_API_KEY`.

```bash
EDITOR_API_KEY=your-generated-key node backend/health-test.js
```

Set `EDITOR_PORT` to change the default listener from `5000`.

Endpoints:

| Endpoint                   | Description                                                                                                   |
| -------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `GET /health-test`         | Validates the editor bridge is reachable. Requires the `x-api-key` header.                                    |
| `POST /cursor-agent`       | Launches the Cursor CLI command configured by `CURSOR_AGENT_COMMAND`. Body must include `{ "query": "..." }`. |
| `GET /task-status?taskId=` | Returns stdout/stderr for previously queued CLI invocations.                                                  |

Configure the static asset directory (`EDITOR_STATIC_DIR`) if you build the editor UI elsewhere.

## Python services

Activate your virtual environment and use the Python entry points in `src/`:

- `python -m src.training.pipeline` – End-to-end training pipeline using configuration schemas. The
  module now logs dataset/train/evaluation timings, computes fairness metrics when a
  `sensitive_attribute` is supplied, and (optionally) records metrics to MLflow if a registry factory
  is provided.
- `python -m src.inference.service` – Launches the inference service (see `src/inference` for configuration details).
- `python -m src.governance.validate` – Runs the governance validation suite.

Use `config/` YAML files to tweak training, metrics, and governance thresholds. The configuration loader enforces schema validation to prevent invalid overrides.

## Knowledge ingestion controls

Knowledge auto-loading is coordinated through `src/knowledge/auto_loader.py`.

- `KNOWLEDGE_AUTO_LOAD=false` disables the watcher entirely.
- `KNOWLEDGE_NDJSON_PATHS` overrides the default NDJSON search paths.
- `KNOWLEDGE_WATCH_INTERVAL` controls how frequently sources are rescanned (leave blank or set to `0` to disable).
- Ignored directories include `.git`, `node_modules`, `cache`, and `__pycache__` to keep scans lightweight.
- When `watchfiles` is available the loader listens for filesystem events; otherwise it falls back to
  periodic scans.

To trigger a manual reload in code:

```python
from src.knowledge.auto_loader import get_auto_loader

auto_loader = get_auto_loader()
await auto_loader.refresh_all_sources()  # Called within an event loop
```

## Cursor auto-invocation

Cursor automation is optional and now non-blocking.

- Toggle with `CURSOR_AUTO_INVOCATION_ENABLED=false`.
- Limit monitored files by setting `CURSOR_FILE_PATTERNS` (defaults to the patterns defined by auto-invocation rules).
- Adjust polling cadence with `CURSOR_MONITOR_INTERVAL` (seconds, default `5`, set to `0` to disable).

The watchers run in the background on the active event loop, so startup scripts like `scripts/codex_cursor_startup.py` now finish promptly instead of hanging on infinite loops.

## Quality assurance

- `make quality` – Runs Node, documentation, and Python suites in one command while saving
  performance metrics to `results/performance/`.
- `python -m src.performance.cli node-quality` – Execute only the Node.js commands (typecheck, lint,
  tests, audit) with timing capture.
- `python -m src.performance.cli docs-quality` – Run Markdown/YAML/editorconfig linting with timing
  capture.
- `python -m src.performance.cli python-quality` – Validate configuration bundles, execute pytest
  with coverage, run Bandit, and audit Python dependencies.
- `python -m src.common.config_loader --json` – Emit a machine-readable report verifying pipeline,
  metrics, and governance configuration files.

Always run the relevant checks before committing to maintain the mixed-language toolchain.
