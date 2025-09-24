# CodexHUB Editor

A web-based workspace controller for CodexHUB with file management, command execution, and optional Cursor agent integration. It exposes an authenticated HTTP API so you can drive local edits from a custom GPT action while still having a desktop-friendly UI.

## Quick start: from desktop to ChatGPT control

1. **Install dependencies**
   ```bash
   pnpm install
   ```
2. **Generate a secure API key**
   ```bash
   pnpm run editor:generate-key
   ```
   Copy the printed `CODEX_API_KEY=...` line into `./.env` next to `package.json`.
3. **(Optional) Configure host/port overrides**
   Set `PORT`, `HOST`, or `CODEX_WORKSPACE_ROOT` in `.env` if you need to expose a different interface or run outside the repo root.
4. **Start the editor**
   - **Windows:** `editor\start-codex.bat`
   - **Any OS:** `pnpm run editor:codex`
5. **Confirm the backend is healthy**
   ```bash
   curl -H "x-api-key: YOUR_KEY" http://localhost:5000/health
   ```
6. **Connect your custom GPT action**
   - Base URL: `http://<host>:<port>` (for example `http://localhost:5000`)
   - Authentication header: `x-api-key: YOUR_KEY`
   - Provide the endpoints listed below so the action can list files, read/write content, and run tasks.
7. **Use the browser UI (optional)**
   Open `http://localhost:5000/editor`, press **⚙️ Connection**, and enter the same base URL and API key so the frontend can issue authenticated requests.

Once these steps succeed, both your desktop browser and GPT action can orchestrate the repository through the same API.

## Environment configuration

### Generate an API key (recommended)

Run the helper script any time you need to rotate credentials:

```bash
pnpm run editor:generate-key
```

The script prints a random key that you should paste into your `.env` file as `CODEX_API_KEY`. Keep this value secret—never commit it.

### Manual `.env` configuration

Create (or update) `./.env` with the following entries:

```bash
CODEX_API_KEY=your_secure_api_key_here
PORT=5000           # optional override
HOST=0.0.0.0        # optional override
CODEX_WORKSPACE_ROOT=/path/to/repo  # optional when running outside the checkout
CURSOR_AGENT_COMMAND=cursor-agent   # optional Cursor CLI hook
CODEX_JSON_LIMIT=10mb               # optional request payload limit
CODEX_FORM_LIMIT=10mb               # optional form payload limit
CODEX_TASK_MAX_BUFFER=10485760      # optional command output buffer (bytes)
CODEX_IGNORE_DIRS=.turbo,.cache     # optional comma separated extra ignore dirs
```

The backend discovers environment files in this order:

1. `CODEX_ENV_PATH` (explicit path)
2. `editor/.env`
3. Repository root `.env`
4. Process environment

> 💡 `CODEX_IGNORE_DIRS` augments the default skip list (`.git`, `node_modules`, `.pnpm-store`, `.next`, `dist`, `build`, `vendor`, `__pycache__`, `.pytest_cache`, `.cache`, `.turbo`, etc.). The search and replace endpoints skip everything in that combined list so large dependency folders do not slow down automation.

### Workspace resolution

Requests are confined to a single workspace root. The server resolves it using:

1. `CODEX_WORKSPACE_ROOT`
2. `GITHUB_WORKSPACE`
3. The directory above `editor/`

Paths that escape this root return `400 Invalid path outside workspace`.

## Starting the editor

### Windows launcher (`start-codex.bat`)

The launcher automates:

- Dependency installation (runs `pnpm install` when `node_modules` is missing)
- Backend startup in its own terminal (`pnpm run editor:codex`)
- Optional tunnel window via `CODEX_TUNNEL_COMMAND` or `CODEX_TUNNEL_CONFIG`
- Browser launch for local and remote URLs
- Warnings when `CODEX_API_KEY` is absent

Environment variables to customize behaviour:

| Variable | Purpose |
| --- | --- |
| `CODEX_TUNNEL_COMMAND` | Exact command to start your tunnel process |
| `CODEX_TUNNEL_CONFIG` | Cloudflare config path used with `cloudflared tunnel --config <path> run` |
| `CODEX_TUNNEL_URL` | Remote URL to open after the tunnel starts |
| `CODEX_BROWSER` | Browser executable path (overrides default) |
| `CODEX_SKIP_TUNNEL` | Set to `1` to skip launching any tunnel |

If neither tunnel variable is set, the script attempts `cloudflared tunnel --url http://localhost:<port>` when `cloudflared` is available.

### Cross-platform manual start

```bash
pnpm install              # only needed once
pnpm run editor:codex     # starts the Express server
```

You can also run the backend entry directly for custom hosts/ports:

```bash
node editor/backend/server.js --host=0.0.0.0 --port=5000
```

## Validate the service

Use these commands after startup (and in automation smoke tests):

```bash
# Health check
curl -H "x-api-key: $CODEX_API_KEY" http://localhost:5000/health

# List the repository root
curl -H "x-api-key: $CODEX_API_KEY" "http://localhost:5000/list?dir=."

# Fetch a file
curl -H "x-api-key: $CODEX_API_KEY" "http://localhost:5000/file?path=README.md"
```

## Connect your custom GPT or automations

### Authentication contract

All API routes expect the header `x-api-key: <CODEX_API_KEY>`. Missing or incorrect keys return `401`/`403`. If the server itself lacks `CODEX_API_KEY`, it responds with `500 Server misconfigured` so you can catch issues early.

### Core API surface

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/list?dir=.` | Enumerate files/directories relative to the workspace |
| GET | `/file?path=<file>` | Retrieve file contents |
| POST | `/file` | Write a file (`{ path, content }`) |
| POST | `/create/file` | Create an empty file |
| POST | `/create/folder` | Create a directory |
| POST | `/delete` | Delete a file/folder (`{ path, recursive }`) |
| POST | `/move` | Move/rename files or folders (`{ src, dest }`) |
| GET | `/search?query=<text>` | Search entire workspace |
| POST | `/replace` | Replace text globally (`{ query, replace }`) |
| POST | `/task/start` | Execute a shell command in the workspace (`{ command }`) |
| GET | `/task/status?taskId=<id>` | Poll the command started above |
| GET | `/git/status` | Run `git status` |
| POST | `/cursor-agent` | Invoke an external Cursor agent command (optional) |

### Example custom action payload

```json
{
  "command": "pnpm test"
}
```

Send this body to `POST /task/start` with the `x-api-key` header. Poll `/task/status?taskId=<returned id>` until `status` is `done` or `failed` and read `stdout`/`stderr` to relay output back to your GPT chat window.

## Browser workflow

- Visit `http://localhost:5000/editor` after the backend starts.
- Press **⚙️ Connection** to enter the base URL and API key (the app only becomes active when both are supplied).
- Manage files, run searches, tail logs, and monitor tasks without hard-coded credentials.

## Troubleshooting

1. **"API key not found"** – regenerate with `pnpm run editor:generate-key`, update `.env`, and restart the server.
2. **`pnpm` missing** – install globally: `npm install -g pnpm`.
3. **Port already in use** – change `PORT` in `.env` or pass `--port` to `server.js`.
4. **Tunnel does not start** – set `CODEX_SKIP_TUNNEL=1` while debugging or provide an explicit `CODEX_TUNNEL_COMMAND`.
5. **Unauthorized responses from GPT action** – confirm the action sends `x-api-key` and that the key matches the server configuration.

## Development

The editor is composed of:

- `codex-editor.js` – Express server exposing filesystem, task, git, and Cursor routes
- `backend/middleware.js` – Shared authentication logic with `.env` discovery
- `codex-editor.html` – Browser UI for manual control and monitoring
- `start-codex.bat` – Windows launcher that prepares dependencies, tunnels, and browser sessions
- `generate-api-key.js` – CLI utility for creating secure API keys

Run tests and linters from the repository root as usual (for example, `pnpm test`, `pnpm lint`).
