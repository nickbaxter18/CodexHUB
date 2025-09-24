"""Tests for the stage detection helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
from utils.stage_detection import (
    BuildStage,
    detect_stage,
    ensure_structure,
    read_stage_marker,
    write_stage_marker,
)


@pytest.fixture()
def tmp_runner(tmp_path: Path) -> Path:
    """Create an isolated runner directory for tests."""

    return ensure_structure(tmp_path)


def test_detect_stage_stage1(tmp_runner: Path) -> None:
    src = tmp_runner / "src"
    (src / "knowledge").mkdir(parents=True)
    (src / "decision").mkdir(parents=True)
    (src / "execution").mkdir(parents=True)
    (src / "knowledge" / "graph.py").write_text(
        "class KnowledgeGraph:\n    def query(self):\n        raise NotImplementedError\n",
        encoding="utf-8",
    )
    (src / "decision" / "mdp.py").write_text(
        "class MDP:\n    def solve(self):\n        raise NotImplementedError\n",
        encoding="utf-8",
    )
    (src / "execution" / "cursor_adapter.py").write_text(
        "class CursorAdapter:\n    async def run(self):\n        raise NotImplementedError\n",
        encoding="utf-8",
    )

    status = detect_stage(tmp_runner)

    assert status.stage is BuildStage.STAGE1
    assert status.marker is None
    assert "knowledge.graph module incomplete" in status.missing_stage_two
    assert status.missing_stage_three
    assert status.next_steps == status.missing_stage_two


def test_detect_stage_stage2(tmp_runner: Path) -> None:
    src = tmp_runner / "src"
    (src / "knowledge").mkdir(parents=True)
    (src / "decision").mkdir(parents=True)
    (src / "execution").mkdir(parents=True)
    (src / "agents").mkdir(parents=True)
    (src / "utils").mkdir(parents=True)
    (src / "api").mkdir(parents=True)

    (src / "knowledge" / "graph.py").write_text(
        "class KnowledgeGraph:\n    def query(self):\n        return {'data': 1}\n",
        encoding="utf-8",
    )
    (src / "knowledge" / "retrieval.py").write_text(
        "def retrieve(graph):\n    return list(graph)\n",
        encoding="utf-8",
    )
    (src / "decision" / "mdp.py").write_text(
        "class MDP:\n    def solve(self):\n        return 42\n",
        encoding="utf-8",
    )
    (src / "decision" / "bayes.py").write_text(
        "def update(prior, likelihood):\n    return prior * likelihood\n",
        encoding="utf-8",
    )
    (src / "decision" / "simulation.py").write_text(
        "def simulate(state):\n    return [state]\n",
        encoding="utf-8",
    )
    (src / "execution" / "cursor_adapter.py").write_text(
        "async def run_cursor():\n    return {'status': 'ok'}\n",
        encoding="utf-8",
    )
    (src / "agents" / "knowledge_agent.py").write_text(
        "class KnowledgeAgent:\n    def observe(self):\n        return {}\n",
        encoding="utf-8",
    )
    (src / "agents" / "decision_agent.py").write_text(
        "class DecisionAgent:\n    def decide(self):\n        return 'run'\n",
        encoding="utf-8",
    )
    (src / "agents" / "collective_agent.py").write_text(
        "class CollectiveAgent:\n    def gather(self):\n        return []\n",
        encoding="utf-8",
    )
    (src / "agents" / "ethics_agent.py").write_text(
        "class EthicsAgent:\n    def approve(self):\n        return True\n",
        encoding="utf-8",
    )
    (src / "utils" / "cache.py").write_text(
        "class Cache:\n    def get(self, key):\n        return None\n",
        encoding="utf-8",
    )
    (src / "agents" / "orchestrator.py").write_text(
        "class Orchestrator:\n"
        "    def __init__(self):\n"
        "        self.knowledge = KnowledgeAgent()\n"
        "        self.decision = DecisionAgent()\n"
        "        self.collective = CollectiveAgent()\n"
        "        self.ethics = EthicsAgent()\n",
        encoding="utf-8",
    )
    (src / "api" / "server.py").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.post('/cursor-run')\n"
        "async def cursor_run():\n"
        "    return {}\n"
        "@app.post('/knowledge/query')\n"
        "async def knowledge_query():\n"
        "    return {}\n"
        "@app.post('/simulate')\n"
        "async def simulate():\n"
        "    return {}\n",
        encoding="utf-8",
    )
    (src / "api" / "schemas.py").write_text(
        "class KnowledgeQueryPayload: ...\n"
        "class SimulationPayload: ...\n"
        "class CursorPayload: ...\n",
        encoding="utf-8",
    )
    (src / "config.py").write_text(
        "simulation_default_runs = 50\n" "fairness_threshold = 0.2\n" "cursor_binary = 'cursor'\n",
        encoding="utf-8",
    )
    (src / "errors.py").write_text(
        "class KnowledgeError(Exception): ...\n"
        "class DecisionError(Exception): ...\n"
        "class EthicsError(Exception): ...\n"
        "class CursorError(Exception): ...\n",
        encoding="utf-8",
    )
    (src / "utils" / "concurrency.py").write_text(
        "def get_executor():\n" "    return None\n" "def run_in_thread():\n" "    return None\n",
        encoding="utf-8",
    )
    (src / "execution" / "git_actions.py").write_text(
        "supported_actions = {'status', 'rebase'}\n",
        encoding="utf-8",
    )

    tests_root = tmp_runner / "tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    for name in [
        "test_knowledge_graph.py",
        "test_decision_agent.py",
        "test_simulation.py",
        "test_cursor_adapter.py",
        "test_ethics_agent.py",
    ]:
        (tests_root / name).write_text(
            "def test_placeholder():\n    assert True\n",
            encoding="utf-8",
        )

    status = detect_stage(tmp_runner)

    assert status.stage is BuildStage.STAGE2
    assert not status.missing_stage_two
    assert status.missing_stage_three
    assert status.next_steps == status.missing_stage_three


def test_detect_stage_stage3() -> None:
    project_root = Path(__file__).resolve().parents[1]
    status = detect_stage(project_root)

    assert status.stage is BuildStage.STAGE3
    assert not status.missing_stage_two
    assert not status.missing_stage_three
    assert status.next_steps == ()


def test_stage_marker_roundtrip(tmp_runner: Path) -> None:
    marker_path = write_stage_marker(tmp_runner, BuildStage.STAGE2)

    assert marker_path.exists()
    assert marker_path.read_text(encoding="utf-8") == BuildStage.STAGE2.marker_name
    assert read_stage_marker(tmp_runner) == BuildStage.STAGE2.marker_name


def test_detect_stage_flags_missing_stage_two_tokens(tmp_runner: Path) -> None:
    src = tmp_runner / "src"
    (src / "api").mkdir(parents=True)
    (src / "api" / "server.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n",
        encoding="utf-8",
    )

    status = detect_stage(tmp_runner)

    assert any("api.server Stage 2 endpoints" in item for item in status.missing_stage_two)
