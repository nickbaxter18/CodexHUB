# API Reference

The CodexHUB workspace exposes a small set of default endpoints and CLI helpers. Extend these definitions as you add new services.

## Node/Express endpoints

| Method | Path            | Description                                                                                                 |
| ------ | --------------- | ----------------------------------------------------------------------------------------------------------- |
| `GET`  | `/health`       | Returns `{ "status": "ok" }` to confirm the Express scaffolding is online.                                  |
| `GET`  | `/health-test`  | Served by `backend/health-test.js`. Requires the `x-api-key` header containing `EDITOR_API_KEY`.            |
| `POST` | `/cursor-agent` | Enqueues a Cursor CLI command (see body schema below). Requires `x-api-key`.                                |
| `GET`  | `/task-status`  | Retrieves stdout/stderr for a Cursor CLI invocation. Requires `x-api-key` and the `taskId` query parameter. |
| `GET`  | `/editor`       | Serves the Codex editor static assets from `EDITOR_STATIC_DIR`.                                             |

### Cursor agent request body

```json
{
  "query": "cursor --example command"
}
```

Response contains a `taskId` that can be polled via `/task-status`.

## Python services

Most Python functionality is exposed through modules or CLIs rather than persistent HTTP servers. Key entry points include:

- `src/training/pipeline.py` – End-to-end model training orchestrator.
- `src/performance/cli.py` – Utility for executing quality suites while persisting timing metrics to
  `results/performance/`.
- `src/inference/inference.py` – Prediction service with caching and concurrency controls.
- `src/governance/privacy.py` / `src/governance/fairness.py` – Enforcement utilities used during CI and validation.

Integrate these modules into your own FastAPI or Flask app as needed. The schemas defined in `src/inference` can be reused for request/response validation.

## Configuration schemas

Configuration files under `config/` are validated by `src/common/config_loader.py` and the associated Pydantic models. Use `python -m src.common.config_loader --help` to inspect available configuration commands.

## Knowledge and Cursor automation controls

- `src/knowledge/auto_loader.py` exposes `start_knowledge_auto_loading()` and `get_auto_loader()` for programmatic ingestion.
- `src/cursor/auto_invocation.py` provides `start_cursor_auto_invocation()` to monitor files and trigger Cursor agents. Environment variables documented in `docs/setup.md` tune polling behavior and scope.

Extend the tables above as you add new HTTP APIs or CLI commands so downstream consumers can discover available functionality.
