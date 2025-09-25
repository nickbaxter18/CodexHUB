# Architecture Overview

Google News Drive Sync is a staged project that grows from a simple monolithic CLI (Stage 1) into a distributed, extensible
system (Stages 2–3). This document summarises the design decisions guiding the initial implementation and highlights
extensibility hooks for later stages.

## Stage 1 – Monolithic Pipeline

Stage 1 delivered a Python CLI that ran end-to-end inside a single process.

1. **Configuration Loader** – `src/utils.py` reads YAML configuration files and prepares runtime settings such as API keys,
   topics, and the Google Drive folder name.
2. **News Fetcher** – `src/news_fetcher.py` interacted with the News API using synchronous HTTP requests. Responses were
   converted into `NewsArticle` dataclass instances with normalised metadata.
3. **Document Formatter** – `src/document_formatter.py` converted the article list into Markdown, generating human-readable
   summaries ready for upload.
4. **Drive Client** – `src/drive_client.py` authenticated with Google Drive via OAuth credentials, ensured that the target folder
   existed, and uploaded the formatted document.
5. **Scheduler** – `src/scheduler.py` offered a lightweight background scheduler for recurring runs based on the configured
   interval.
6. **Entry Point** – `src/main.py` orchestrated the workflow, handled errors and logged progress.

## Stage 2 – System Refinement

Stage 2 upgrades the monolith with concurrency, multi-source aggregation and better operational hygiene while keeping a
single deployable unit.

1. **Asynchronous Fetching** – `src/news_fetcher.py` now exposes an asyncio-powered client that concurrently pulls per-topic
   pages from NewsAPI. `src/rss_fetcher.py` adds RSS ingestion with matching dataclasses.
2. **Aggregation & Deduplication** – `src/api_router.py` orchestrates NewsAPI and RSS tasks, deduplicating results and piping
   them into the document formatter.
3. **Caching** – `src/cache.py` stores article fingerprints in SQLite, preventing duplicate uploads and enabling configurable
   retention windows.
4. **Secret Management & Encryption** – `src/utils.py` loads optional `.env` files and provides a `TokenEncryptor` used by
   `TokenStorage` in `src/drive_client.py` to encrypt stored OAuth tokens.
5. **Monitoring** – `src/monitor.py` tracks lightweight metrics (articles processed, error counts) for future observability
   integrations.
6. **Scheduling Upgrade** – `src/scheduler.py` now prefers APScheduler, falling back to the Stage 1 threaded implementation
   when the dependency is unavailable.
7. **Entry Point Enhancements** – `src/main.py` coordinates cache initialisation, monitoring, asynchronous article retrieval
   and Drive uploads while supporting cron-style triggers.

## Stage 3 – Dashboard & Extensibility

Stage 3 completes the evolution into a user-facing system with pluggable sources and observability.

1. **Article Repository** – `src/article_repository.py` persists article metadata to SQLite so both the document formatter and
   dashboard can reuse the same canonical dataset.
2. **Plugin Loader** – `src/plugin_manager.py` and `src/plugins/` dynamically discover Python-based news sources. Administrators
   can add new sources by dropping modules onto the filesystem or referencing importable packages in configuration.
3. **Monitoring Upgrades** – `src/monitor.py` now tracks pipeline runs, document uploads and renders Prometheus metrics for
   `/metrics` scraping. Metrics are consumed by the dashboard and exported for observability stacks.
4. **FastAPI Server** – `src/server.py` exposes REST endpoints and health probes that surface aggregated articles, source
   listings and monitoring data. `src/main.py` can launch the server in parallel with the scheduler via the `--serve` flag.
5. **Web Dashboard** – `ui/` hosts a React + Tailwind UI offering search, filtering, keyboard navigation and high-contrast
   theming for accessibility. Components consume the FastAPI endpoints and present a responsive news experience.

## Deployment Considerations

- Run the CLI as a cron job or containerised task for periodic execution.
- Provide environment variables or secret management for sensitive credentials.
- Log execution details to aid debugging and monitoring.

## Testing Strategy

Automated tests reside under `tests/` and use mocks to isolate external dependencies. They cover success and failure cases for
API calls, document formatting, Drive interactions, the scheduler and end-to-end orchestration.
