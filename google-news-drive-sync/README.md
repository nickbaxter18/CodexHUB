# Google News Drive Sync

Google News Drive Sync automates the ingestion of current news articles and stores them in a Google Drive folder. It pulls
articles from a configurable third-party API, formats them into reader-friendly Markdown documents and uploads them to a Drive
folder for downstream consumption by analytics teams, AI researchers and automation workflows.

## Features

- Asynchronously fetches headlines from NewsAPI with per-topic concurrency.
- Aggregates RSS feeds alongside API responses, deduplicates the combined results and records them in a SQLite repository.
- Plugin loader discovers custom fetchers at runtime so new sources can be added without touching core code.
- FastAPI dashboard exposes `/articles`, `/sources`, `/status`, `/metrics` and `/health` endpoints for downstream systems.
- React-based UI (under `ui/`) provides a searchable, accessible feed for analysts and stakeholders.
- Persists seen articles and stores pipeline metrics to drive both deduplication and observability dashboards.
- Encrypts optional Drive tokens at rest and loads secrets from environment variables or `.env` files.
- Uses APScheduler (with a thread-based fallback) for recurring or cron-based synchronisation.

## Project Structure

```
.
├── README.md
├── config/
│   └── config.yaml
├── docs/
│   └── architecture.md
├── metadata/
│   └── stage.json
├── scripts/
│   └── run_sync.sh
├── src/
│   ├── __init__.py
│   ├── api_router.py
│   ├── article_repository.py
│   ├── cache.py
│   ├── document_formatter.py
│   ├── drive_client.py
│   ├── main.py
│   ├── monitor.py
│   ├── news_fetcher.py
│   ├── plugin_manager.py
│   ├── plugins/
│   │   └── sample_plugin.py
│   ├── rss_fetcher.py
│   ├── scheduler.py
│   ├── server.py
│   └── utils.py
├── ui/
│   ├── package.json
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── ArticleList.tsx
│       │   ├── ArticlePreview.tsx
│       │   └── SearchBar.tsx
│       └── main.tsx
└── tests/
    ├── __init__.py
    ├── test_api_router.py
    ├── test_article_repository.py
    ├── test_cache.py
    ├── test_document_formatter.py
    ├── test_drive_client.py
    ├── test_integration.py
    ├── test_monitor.py
    ├── test_news_fetcher.py
    ├── test_plugin_manager.py
    ├── test_rss_fetcher.py
    ├── test_scheduler.py
    └── test_server.py
```

## Getting Started

1. Create and populate `config/config.yaml` with your API keys, query parameters, RSS feeds and Google Drive settings. See the example in this
   repository for the expected structure. **Do not commit real credentials.** You may also reference a `.env` file for sensitive values.
2. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # customise as needed for Google API clients
```

3. Run the synchronisation manually:

```bash
python -m src.main --config config/config.yaml
```

The script loads the configuration, fetches news articles, formats them and uploads the resulting document to Google Drive.

### Dashboard & API

Expose the FastAPI dashboard and Prometheus metrics alongside the scheduler by supplying the `--serve` flag:

```bash
python -m src.main --config config/config.yaml --serve --host 0.0.0.0 --port 8080
```

The API surfaces:

- `GET /articles` – Paginated article feed with optional `source` and `q` filters.
- `GET /sources` – Distinct list of configured sources.
- `GET /status` – Combined repository statistics and monitoring counters.
- `GET /metrics` – Prometheus-formatted metrics.
- `GET /health` – Lightweight health probe for orchestrators.

### Web UI

The React dashboard in `ui/` consumes the API and renders a searchable news feed with accessible components:

```bash
cd ui
pnpm install
pnpm run dev
```

The UI uses Tailwind CSS and Material-inspired components with keyboard navigation, ARIA labelling and high-contrast theme support.

## Running Tests

Execute the unit test suite and lint checks before contributing changes:

```bash
python -m pytest tests/
flake8 src/
python -m ruff check src/ tests/
```

## Scheduling

To run the synchronisation at regular intervals, configure `scheduler.update_interval_minutes` or provide a cron expression via
`scheduler.cron` in `config/config.yaml`. APScheduler powers the recurring execution when available; otherwise the project falls
back to a lightweight threaded scheduler. `scripts/run_sync.sh` remains available for ad-hoc execution from cron or other
orchestrators.

## Security Considerations

- Store API keys and OAuth credentials outside version control (e.g., environment variables, `.env` files excluded from commits or secret managers).
- Provide a `TOKEN_ENCRYPTION_KEY` environment variable (or configure `secrets.encryption_key`) to encrypt stored Drive tokens.
- Respect the terms of service for the news API and Google Drive while limiting article volume to stay within rate limits and storage budgets.

## Future Enhancements

- Ship optional summarisation plugins that use LLMs to condense long-form articles before upload.
- Extend the dashboard with authentication and per-user preferences.
- Introduce performance and load tests for the FastAPI layer alongside bundle-size budgets for the UI.
