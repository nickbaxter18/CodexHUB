# Setup Guide

This guide explains how to bootstrap a development environment for CodexHUB without relying on Cursor-specific automation. Follow the steps below the first time you clone the repository.

## 1. Install system dependencies

- **Node.js** 20 or newer (matches the version required in `README.md` and the workspace `engines` constraint).
- **pnpm** 8 or newer. If you use Corepack, run `corepack enable pnpm` to activate the bundled version.
- **Python** 3.11 (matches the versions configured in `pyproject.toml`).
- **Docker** 24+ (optional) for containerized deployments.

## 2. Clone the repository

```bash
git clone https://github.com/nickbaxter18/CodexHUB.git
cd CodexHUB
```

## 3. Bootstrap dependencies

Run the unified bootstrap script to install Node packages, create a virtual environment, and install Python dependencies:

```bash
pnpm run setup
```

Additional flags let you tailor the bootstrap process:

- `--skip-node` – reuse existing `node_modules` without invoking pnpm.
- `--skip-python` – skip virtual environment creation and Python dependency installation.
- `--no-dev-extras` – install only runtime Python dependencies.
- `--venv path/to/.venv` – override the default virtual environment location.

If you want to hydrate optional pnpm workspaces (for example the Next.js editor) run a filtered install afterwards, e.g. `pnpm install --filter apps/editor...`.

## 5. Configure environment variables

Create a `.env` file (or export variables in your shell) with the following keys:

| Variable                         | Description                                                                                                     |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `EDITOR_API_KEY`                 | Required for the editor health-test endpoints. Generate securely and never commit it to source control.         |
| `EDITOR_STATIC_DIR`              | Optional override pointing to the compiled editor assets. Defaults to `editor/` inside the repository.          |
| `EDITOR_PORT`                    | Overrides the listening port for `backend/health-test.js` (default `5000`).                                     |
| `CURSOR_AGENT_COMMAND`           | Optional command used by the health-test bridge to launch the Cursor CLI. Defaults to `cursor-agent`.           |
| `CURSOR_AGENT_CWD`               | Working directory used when spawning the Cursor CLI. Defaults to the repository root.                           |
| `KNOWLEDGE_AUTO_LOAD`            | Set to `false` to disable automatic knowledge ingestion.                                                        |
| `KNOWLEDGE_NDJSON_PATHS`         | Comma-separated list of NDJSON files or directories to ingest.                                                  |
| `KNOWLEDGE_WATCH_INTERVAL`       | Polling interval (seconds) for reloading knowledge sources. Leave blank (or set to `0`) to disable the watcher. |
| `CURSOR_AUTO_INVOCATION_ENABLED` | Disable Cursor auto-invocation when set to `false`.                                                             |
| `CURSOR_FILE_PATTERNS`           | Comma-separated glob patterns limiting the files monitored for auto-invocation.                                 |
| `CURSOR_MONITOR_INTERVAL`        | Polling interval (seconds) for auto-invocation file checks. Set to `0` to disable the watcher.                  |

You can manage secrets locally with tools such as `direnv`, `doppler`, or the secret manager used by your deployment platform.

## 6. Verify the toolchain

Run a quick smoke test to confirm both ecosystems are healthy:

```bash
pnpm run lint
pnpm test
python -m pytest
```

Resolve any lint or test failures before starting feature work.

## 7. Optional: Docker workflow

To build and run the Docker image:

```bash
pnpm install  # Ensure lockfile is fresh
docker build -t codexhub .
docker run --env-file .env -p 4000:4000 codexhub
```

The Dockerfile uses pnpm for dependency installation and copies the entire workspace into the container. Provide environment variables at runtime to inject secrets securely.
