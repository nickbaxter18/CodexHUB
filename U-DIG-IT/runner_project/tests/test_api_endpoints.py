import json
import time
from pathlib import Path
from typing import Any, Dict, cast
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.api.server import app

client = TestClient(app)


def wait_for_task(task_id: str, timeout: float = 3.0) -> Dict[str, Any]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = client.get(f"/tasks/{task_id}")
        if response.status_code == 200:
            body = cast(Dict[str, Any], response.json())
            if body["status"] in {"completed", "failed"}:
                return body
        time.sleep(0.05)
    raise AssertionError("Task did not complete in time")


def test_run_command_endpoint() -> None:
    response = client.post(
        "/run-command",
        json={"command": "echo", "args": ["api-test"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    task = wait_for_task(body["id"])
    assert task["status"] == "completed"
    assert "api-test" in task["result"]["stdout"]
    assert "decision" in task["result"]
    assert "ethics" in task["result"]


def test_run_command_invalid_command() -> None:
    response = client.post("/run-command", json={"command": "rm"})
    assert response.status_code == 200
    body = response.json()
    task = wait_for_task(body["id"])
    assert task["status"] == "failed"
    assert task["error"]


def test_list_tasks_endpoint() -> None:
    response = client.get("/tasks")
    assert response.status_code == 200
    body = response.json()
    assert "tasks" in body


def test_cursor_endpoint(monkeypatch: Any) -> None:
    creation = type(
        "TaskCreation",
        (),
        {"task_id": "cursor123", "status": type("Status", (), {"value": "pending"})()},
    )()

    with patch(
        "src.api.server.ORCHESTRATOR.schedule_cursor_action", AsyncMock(return_value=creation)
    ):
        response = client.post("/cursor-run", json={"prompt": "hello"})
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "cursor123"
    assert body["status"] == "pending"


def test_knowledge_and_simulation_endpoints(monkeypatch: Any, tmp_path: Path) -> None:
    data = tmp_path / "knowledge.ndjson"
    data.write_text(
        json.dumps(
            {"doc_id": "a", "title": "Alpha", "text": "probability theory", "tags": ["math"]}
        )
        + "\n"
    )
    monkeypatch.setenv("RUNNER_KNOWLEDGE_SOURCES", json.dumps([str(data)]))
    from src import config
    from src.knowledge import retrieval

    config.get_config.cache_clear()
    retrieval.clear_cache()

    response = client.post("/knowledge/query", json={"query": "probability", "limit": 2})
    assert response.status_code == 200
    results = response.json()["results"]
    assert results and results[0]["id"] == "a"

    sim_payload = {
        "outcomes": [1.0, 0.0],
        "probabilities": [0.7, 0.3],
        "runs": 50,
    }
    response = client.post("/simulate", json=sim_payload)
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["expectation"] <= 1

    config.get_config.cache_clear()
    retrieval.clear_cache()
