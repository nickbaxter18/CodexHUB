# Google News Drive Sync

Google News Drive Sync automates the ingestion of current news articles and stores them in a Google Drive folder. It pulls
articles from a configurable third-party API, formats them into reader-friendly Markdown documents and uploads them to a Drive
folder for downstream consumption by analytics teams, AI researchers and automation workflows.

## Features

- Fetches the latest headlines from a configurable news API using per-topic queries.
- Formats articles into Markdown documents with consistent structure and metadata.
- Uploads generated documents to a target Google Drive folder via OAuth credentials.
- Provides a lightweight scheduler for recurring synchronisation jobs.

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
│   ├── document_formatter.py
│   ├── drive_client.py
│   ├── main.py
│   ├── news_fetcher.py
│   ├── scheduler.py
│   └── utils.py
└── tests/
    ├── __init__.py
    ├── test_document_formatter.py
    ├── test_drive_client.py
    ├── test_integration.py
    ├── test_news_fetcher.py
    └── test_scheduler.py
```

## Getting Started

1. Create and populate `config/config.yaml` with your API keys, query parameters and Google Drive settings. See the example in this
   repository for the expected structure. **Do not commit real credentials.**
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

## Running Tests

Execute the unit test suite and lint checks before contributing changes:

```bash
python -m pytest tests/
flake8 src/
```

## Scheduling

To run the synchronisation at regular intervals, configure the `update_interval_minutes` value in `config/config.yaml`. You can
also invoke `scripts/run_sync.sh` from cron or another scheduling system to trigger the pipeline on demand.

## Security Considerations

- Store API keys and OAuth credentials outside version control (e.g., environment variables or secret managers).
- Respect the terms of service for the news API and Google Drive.
- Limit the number of fetched articles to stay within API rate limits and avoid excessive Drive storage usage.

## Future Enhancements

Stage 2 and Stage 3 will extend the project with asynchronous fetching, multi-source aggregation, user-facing dashboards and a
plugin architecture for new sources.
