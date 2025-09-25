# Architecture Overview

Google News Drive Sync is a staged project that grows from a simple monolithic CLI (Stage 1) into a distributed, extensible
system (Stages 2–3). This document summarises the design decisions guiding the initial implementation and highlights
extensibility hooks for later stages.

## Stage 1 – Monolithic Pipeline

Stage 1 delivers a Python CLI that runs end-to-end inside a single process.

1. **Configuration Loader** – `src/utils.py` reads YAML configuration files and prepares runtime settings such as API keys,
   topics, and the Google Drive folder name.
2. **News Fetcher** – `src/news_fetcher.py` interacts with the News API using HTTP GET requests. Responses are converted into
   `NewsArticle` dataclass instances with normalised metadata.
3. **Document Formatter** – `src/document_formatter.py` converts the article list into Markdown, generating human-readable
   summaries ready for upload.
4. **Drive Client** – `src/drive_client.py` authenticates with Google Drive via OAuth credentials, ensures that the target folder
   exists, and uploads the formatted document.
5. **Scheduler** – `src/scheduler.py` offers a lightweight background scheduler for recurring runs based on the configured
   interval.
6. **Entry Point** – `src/main.py` orchestrates the workflow, handles errors and logs progress.

## Future Stages

- **Stage 2** introduces asynchronous fetching, caching and multi-source aggregation using additional modules such as
  `src/rss_fetcher.py` and `src/cache.py`.
- **Stage 3** adds a FastAPI backend, React dashboard and plugin loader to deliver a user-friendly interface and observability.

## Deployment Considerations

- Run the CLI as a cron job or containerised task for periodic execution.
- Provide environment variables or secret management for sensitive credentials.
- Log execution details to aid debugging and monitoring.

## Testing Strategy

Automated tests reside under `tests/` and use mocks to isolate external dependencies. They cover success and failure cases for
API calls, document formatting, Drive interactions, the scheduler and end-to-end orchestration.
