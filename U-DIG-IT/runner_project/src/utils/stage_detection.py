"""Utilities for detecting the runner build stage.

The automation blueprint shipped with the repository requires Codex to
inspect the runner source tree at the beginning of every task.  This module
packages that behaviour so that it can be reused from scripts, tests or
future automation hooks.  Stage detection follows the definitions in
``COMMAND_PROMPTS.md``:

* **Stage 1** – core skeleton in place but key modules are still stubs that
  raise :class:`NotImplementedError`.
* **Stage 2** – knowledge, decision and cursor modules are populated but the
  user interface and plugin loader are not yet available.
* **Stage 3** – all Stage 2 features plus the dashboard UI and dynamic plugin
  system are present.

In addition to detecting the current stage, the helper functions here can
ensure the expected directory layout exists and maintain the optional
``.stage_complete`` marker file mentioned in the blueprint.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional, Sequence

__all__ = [
    "BuildStage",
    "StageStatus",
    "ensure_structure",
    "detect_stage",
    "read_stage_marker",
    "write_stage_marker",
]


class BuildStage(Enum):
    """Enumeration of the runner build stages."""

    STAGE1 = 1
    STAGE2 = 2
    STAGE3 = 3

    @property
    def marker_name(self) -> str:
        """Return the canonical marker filename for the stage."""

        return f"stage{self.value}_complete"


@dataclass
class StageStatus:
    """Outcome returned by :func:`detect_stage`.

    The status bundles the inferred :class:`BuildStage`, any persisted marker
    and the outstanding feature work required to progress through the
    blueprint.  Automation can use :attr:`next_steps` to surface actionable
    tasks for the runner build.
    """

    stage: BuildStage
    marker: Optional[str] = None
    missing_stage_two: tuple[str, ...] = ()
    missing_stage_three: tuple[str, ...] = ()

    def __str__(self) -> str:  # pragma: no cover - convenience only
        marker = f" ({self.marker})" if self.marker else ""
        return f"Stage {self.stage.value}{marker}"

    @property
    def next_steps(self) -> tuple[str, ...]:
        """Return actionable work items to advance to the next stage."""

        if self.stage is BuildStage.STAGE1:
            return self.missing_stage_two
        if self.stage is BuildStage.STAGE2:
            return self.missing_stage_three
        return ()


def ensure_structure(repo_root: Path) -> Path:
    """Ensure the base folder layout exists and return the project root.

    Parameters
    ----------
    repo_root:
        Root directory of the repository that should contain ``U-DIG-IT``.

    Returns
    -------
    Path
        The path to ``U-DIG-IT/runner_project`` within ``repo_root``.
    """

    base = repo_root / "U-DIG-IT"
    base.mkdir(parents=True, exist_ok=True)
    project_root = base / "runner_project"
    project_root.mkdir(parents=True, exist_ok=True)
    return project_root


def detect_stage(project_root: Path) -> StageStatus:
    """Inspect the runner source tree and infer the current build stage."""

    src_root = project_root / "src"
    marker = read_stage_marker(project_root)
    missing_stage_two = tuple(_missing_stage_two_features(src_root))
    missing_stage_three = tuple(_missing_stage_three_features(src_root))

    if not missing_stage_two and not missing_stage_three:
        stage = BuildStage.STAGE3
    elif not missing_stage_two:
        stage = BuildStage.STAGE2
    else:
        stage = BuildStage.STAGE1

    return StageStatus(
        stage=stage,
        marker=marker,
        missing_stage_two=missing_stage_two,
        missing_stage_three=missing_stage_three,
    )


def read_stage_marker(project_root: Path) -> Optional[str]:
    """Read the optional ``.stage_complete`` marker if present."""

    marker_file = project_root / ".stage_complete"
    if not marker_file.exists():
        return None
    content = marker_file.read_text(encoding="utf-8").strip()
    return content or None


def write_stage_marker(project_root: Path, stage: BuildStage) -> Path:
    """Write the marker file documenting the latest completed stage."""

    marker_file = project_root / ".stage_complete"
    marker_file.write_text(stage.marker_name, encoding="utf-8")
    return marker_file


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _missing_stage_two_features(src_root: Path) -> list[str]:
    """Return human-readable descriptions of missing Stage 2 work."""

    requirements: dict[str, Path] = {
        "knowledge.graph module": src_root / "knowledge" / "graph.py",
        "knowledge.retrieval module": src_root / "knowledge" / "retrieval.py",
        "decision.mdp module": src_root / "decision" / "mdp.py",
        "decision.bayes module": src_root / "decision" / "bayes.py",
        "decision.simulation module": src_root / "decision" / "simulation.py",
        "agents.knowledge_agent module": src_root / "agents" / "knowledge_agent.py",
        "agents.decision_agent module": src_root / "agents" / "decision_agent.py",
        "agents.collective_agent module": src_root / "agents" / "collective_agent.py",
        "agents.ethics_agent module": src_root / "agents" / "ethics_agent.py",
        "execution.cursor_adapter module": src_root / "execution" / "cursor_adapter.py",
        "utils.cache module": src_root / "utils" / "cache.py",
    }

    token_requirements: dict[str, tuple[Path, Sequence[str]]] = {
        "agents.orchestrator integration": (
            src_root / "agents" / "orchestrator.py",
            ("KnowledgeAgent", "DecisionAgent", "CollectiveAgent", "EthicsAgent"),
        ),
        "api.server Stage 2 endpoints": (
            src_root / "api" / "server.py",
            ("/cursor-run", "/knowledge/query", "/simulate"),
        ),
        "api.schemas Stage 2 payloads": (
            src_root / "api" / "schemas.py",
            ("KnowledgeQueryPayload", "SimulationPayload", "CursorPayload"),
        ),
        "config Stage 2 settings": (
            src_root / "config.py",
            (
                "simulation_default_runs",
                "fairness_threshold",
                "cursor_binary",
            ),
        ),
        "errors Stage 2 error classes": (
            src_root / "errors.py",
            ("KnowledgeError", "DecisionError", "EthicsError", "CursorError"),
        ),
        "utils.concurrency helpers": (
            src_root / "utils" / "concurrency.py",
            ("get_executor", "run_in_thread"),
        ),
        "execution.git_actions advanced operations": (
            src_root / "execution" / "git_actions.py",
            ("supported_actions", "rebase"),
        ),
    }

    tests_root = src_root.parent / "tests"
    test_requirements: dict[str, Path] = {
        "tests.test_knowledge_graph suite": tests_root / "test_knowledge_graph.py",
        "tests.test_decision_agent suite": tests_root / "test_decision_agent.py",
        "tests.test_simulation suite": tests_root / "test_simulation.py",
        "tests.test_cursor_adapter suite": tests_root / "test_cursor_adapter.py",
        "tests.test_ethics_agent suite": tests_root / "test_ethics_agent.py",
    }

    missing: list[str] = []
    for label, path in requirements.items():
        if not path.exists():
            missing.append(f"{label} missing")
        elif not _is_meaningful(path):
            missing.append(f"{label} incomplete")

    for label, (path, tokens) in token_requirements.items():
        if not path.exists():
            missing.append(f"{label} missing")
        elif not _file_contains_all(path, tokens):
            missing.append(f"{label} incomplete")

    for label, path in test_requirements.items():
        if not path.exists():
            missing.append(f"{label} missing")
        elif not _is_meaningful(path):
            missing.append(f"{label} incomplete")
    return missing


def _missing_stage_three_features(src_root: Path) -> list[str]:
    """Return human-readable descriptions of missing Stage 3 work."""

    ui_dir = src_root / "ui"
    template_dir = ui_dir / "templates"
    requirements: dict[str, Path] = {
        "ui.dashboard module": ui_dir / "dashboard.py",
        "utils.plugin_loader module": src_root / "utils" / "plugin_loader.py",
        "utils.observer module": src_root / "utils" / "observer.py",
        "plugins package": src_root / "plugins" / "__init__.py",
    }

    missing: list[str] = []

    if not ui_dir.exists():
        missing.append("ui directory missing")
    else:
        dashboard_path = requirements.pop("ui.dashboard module")
        if not dashboard_path.exists():
            missing.append("ui.dashboard module missing")
        elif not _is_meaningful(dashboard_path):
            missing.append("ui.dashboard module incomplete")

    if not template_dir.exists():
        missing.append("ui.templates directory missing")
    elif not any(template_dir.glob("*.html")):
        missing.append("ui.templates missing HTML templates")

    for label, path in requirements.items():
        if not path.exists():
            missing.append(f"{label} missing")
        elif not _is_meaningful(path):
            missing.append(f"{label} incomplete")

    token_requirements: dict[str, tuple[Path, Sequence[str]]] = {
        "api.server Stage 3 endpoints": (
            src_root / "api" / "server.py",
            ("/dashboard", "/plugins", "/health"),
        ),
        "api.schemas Stage 3 payloads": (
            src_root / "api" / "schemas.py",
            ("PluginListResponse", "PluginTogglePayload", "HealthResponse"),
        ),
        "types Stage 3 dataclasses": (
            src_root / "types.py",
            ("DashboardSnapshot", "PluginMetadata", "HealthReport"),
        ),
        "agents.orchestrator Stage 3 routines": (
            src_root / "agents" / "orchestrator.py",
            ("dashboard_snapshot", "render_dashboard", "reload_plugins", "health_report"),
        ),
    }

    for label, (path, tokens) in token_requirements.items():
        if not path.exists():
            missing.append(f"{label} missing")
        elif not _file_contains_all(path, tokens):
            missing.append(f"{label} incomplete")

    tests_root = src_root.parent / "tests"
    stage_three_tests: dict[str, Path] = {
        "tests.test_ui suite": tests_root / "test_ui.py",
        "tests.test_plugins suite": tests_root / "test_plugins.py",
        "tests.test_resilience suite": tests_root / "test_resilience.py",
    }

    for label, path in stage_three_tests.items():
        if not path.exists():
            missing.append(f"{label} missing")
        elif not _is_meaningful(path):
            missing.append(f"{label} incomplete")

    return missing


def _is_meaningful(path: Path) -> bool:
    """Heuristic to decide whether a module contains real logic."""

    text = path.read_text(encoding="utf-8") if path.exists() else ""
    stripped = text.strip()
    if not stripped:
        return False
    if "NotImplementedError" in stripped and "tests" not in path.parts:
        return False
    # Consider the module meaningful as soon as it contains any executable code.
    for line in stripped.splitlines():
        candidate = line.strip()
        if not candidate or candidate.startswith(("#", '"')):
            continue
        return True
    return False


def _has_stage_three_features_in_sources(paths: Iterable[Path]) -> bool:
    """Compatibility shim for older automation hooks."""

    return any(
        not _missing_stage_two_features(path) and not _missing_stage_three_features(path)
        for path in paths
    )


def _file_contains_all(path: Path, tokens: Sequence[str]) -> bool:
    """Return ``True`` when the file contains every token in ``tokens``."""

    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return all(token in text for token in tokens)
