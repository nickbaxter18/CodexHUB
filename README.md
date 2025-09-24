# CodexHUB

CodexHUB is a hybrid Node.js and Python workspace for building, governing, and serving AI-assisted developer workflows. The repository pairs an Express-based orchestration layer with a schema-driven Python ML pipeline that handles ingestion, training, governance, and inference.

## Repository Layout

- `src/` – Node services, Express entry points, and shared utilities.
- `backend/` – Development helpers for the web-based Codex editor and local automation hooks.
- `agents/`, `meta_agent/`, `macro_system/` – Specialist AI agents, macro tooling, and coordination logic.
- `qa/`, `tests/` – Quality gates, governance checks, and automated verification suites.
- `docs/` – Living documentation for setup, API usage, governance, and architecture.
- `scripts/` – Automation helpers for Cursor, knowledge ingestion, and repo health checks.

## Prerequisites

- Node.js 18+
- pnpm 8+ (Corepack users can enable with `corepack enable`)
- Python 3.11 with `pip` (virtual environments recommended)
- Optional: Docker 24+ for containerized deployments

## Getting Started

### 1. Install dependencies

```bash
pnpm install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure environment variables

Copy `.env.example` (if present) or create a new `.env` file to supply:

- `EDITOR_API_KEY` – Required for the editor health test endpoints.
- `EDITOR_STATIC_DIR` – Optional override for hosting pre-built editor assets.
- `CURSOR_AGENT_COMMAND` / `CURSOR_AGENT_CWD` – Optional overrides for invoking the Cursor agent CLI.
- See `docs/setup.md` for a full list of runtime configuration options.

### 3. Run services

- **Express scaffolding**: `pnpm run dev` starts the Node entry point on port `4000`.
- **Editor health server**: `node backend/health-test.js` exposes `/health-test`, `/cursor-agent`, and `/task-status` guarded by `EDITOR_API_KEY`.
- **Python pipeline**: activate your virtual environment and run the relevant modules, e.g. `python -m src.training.pipeline` or `python -m src.inference.service`. Detailed workflows live in `docs/usage.md`.

### 4. Quality checks

```bash
pnpm run lint
pnpm test
python -m pytest
pnpm run codex:status
```

Additional commands for formatting, security scanning, and governance validation are documented in `docs/usage.md`.

## Documentation

- [Setup Guide](docs/setup.md) – System requirements, environment bootstrapping, and dependency management.
- [Usage Guide](docs/usage.md) – Running services, orchestrating training, and common developer tasks.
- [API Reference](docs/api.md) – Available endpoints and CLI commands.
- [Architecture](docs/architecture.md) – High-level diagrams and module responsibilities.
- [Governance](docs/GOVERNANCE.md) – Fairness, privacy, and compliance controls.

## Security Notes

Hard-coded credentials have been removed in favor of environment variables. Rotate any previously committed secrets and follow the guidance in `SECURITY.md` for secret management and operational hardening.

## Contributing

Please review `CONTRIBUTING.md` and the checks listed above before opening a pull request. Run `pnpm test` and `python -m pytest` locally to keep the mixed Node/Python toolchain healthy.
