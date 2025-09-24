import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src import config
from src.api.server import app
from src.knowledge import retrieval


@pytest.mark.asyncio
async def test_dashboard_endpoints(monkeypatch: Any, tmp_path: Path) -> None:
    dataset = tmp_path / "knowledge.ndjson"
    dataset.write_text(
        "\n".join(
            [
                json.dumps({"doc_id": "x", "title": "Node X", "text": "probability graph"}),
                json.dumps({"doc_id": "y", "title": "Node Y", "text": "graph theory"}),
            ]
        )
    )
    monkeypatch.setenv("RUNNER_KNOWLEDGE_SOURCES", json.dumps([str(dataset)]))
    config.get_config.cache_clear()
    retrieval.clear_cache()

    with TestClient(app) as client:
        overview = client.get("/dashboard/overview")
        assert overview.status_code == 200
        data = overview.json()
        assert "total_tasks" in data
        assert "knowledge_nodes" in data

        html_response = client.get("/dashboard")
        assert html_response.status_code == 200
        assert "Runner Dashboard" in html_response.text

    config.get_config.cache_clear()
    retrieval.clear_cache()
