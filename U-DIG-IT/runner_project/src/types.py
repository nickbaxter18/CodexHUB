"""Shared datatypes for the runner."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CommandRequest:
    command: str
    args: Sequence[str] = field(default_factory=list)
    cwd: Optional[Path] = None
    timeout: Optional[float] = None


@dataclass
class CommandResult:
    stdout: str
    stderr: str
    return_code: int
    started_at: datetime
    completed_at: datetime


@dataclass
class GitActionRequest:
    action: str
    args: Sequence[str] = field(default_factory=list)
    cwd: Optional[Path] = None
    timeout: Optional[float] = None


@dataclass
class GitActionResult:
    stdout: str
    stderr: str
    return_code: int
    action: str
    started_at: datetime
    completed_at: datetime


@dataclass
class KnowledgeQueryRequest:
    query: str
    limit: int = 5


@dataclass
class KnowledgeQueryResult:
    results: List[Dict[str, Any]]


@dataclass
class SimulationRequest:
    outcomes: Sequence[float]
    probabilities: Sequence[float]
    runs: int = 100
    transition_matrix: Optional[Dict[str, Dict[str, float]]] = None
    initial_state: Optional[str] = None
    steps: Optional[int] = None


@dataclass
class SimulationResult:
    expectation: float
    samples: List[float]
    markov_path: Optional[List[str]] = None


@dataclass
class CursorInvocationRequest:
    prompt: str
    file_path: Optional[Path] = None
    apply_changes: bool = False
    extra_args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CursorInvocationResult:
    stdout: str
    stderr: str
    return_code: int
    suggestions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    result: Optional[Any] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if self.result is not None:
            data["result"] = self.result
        if self.error is not None:
            data["error"] = self.error
        return data


@dataclass
class TaskCreation:
    task_id: str
    status: TaskStatus


@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskList:
    tasks: List[Task]

    def to_dict(self) -> Dict[str, Any]:
        return {"tasks": [task.to_dict() for task in self.tasks]}


@dataclass
class PluginMetadata:
    """Metadata describing a dynamically loaded plugin."""

    name: str
    description: str = ""
    version: str = "0.0.0"
    enabled: bool = True
    entrypoint: Optional[str] = None


@dataclass
class PluginOperationResult:
    """Result payload returned after mutating plugin state."""

    name: str
    status: str
    detail: str = ""


@dataclass
class DashboardSnapshot:
    """Aggregate data rendered on the Stage 3 dashboard."""

    generated_at: datetime
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    active_plugins: List[PluginMetadata]
    knowledge_nodes: int
    knowledge_edges: int
    fairness_threshold: float
    dynamic_fairness: float
    collective_opt_in: bool


@dataclass
class HealthCheck:
    """Individual health check result."""

    name: str
    status: str
    detail: str = ""


@dataclass
class HealthReport:
    """Aggregated health information for the runner."""

    generated_at: datetime
    status: str
    checks: List[HealthCheck]
