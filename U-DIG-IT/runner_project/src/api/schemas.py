"""Pydantic schemas for the API."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from ..types import (
    CommandRequest,
    CursorInvocationRequest,
    DashboardSnapshot,
    GitActionRequest,
    HealthCheck,
    HealthReport,
    KnowledgeQueryRequest,
    PluginMetadata,
    SimulationRequest,
    Task,
)


class CommandPayload(BaseModel):
    command: str = Field(..., description="Whitelisted command to execute")
    args: List[str] = Field(default_factory=list)
    cwd: Optional[Path] = Field(default=None, description="Working directory")
    timeout: Optional[float] = Field(default=None, ge=0)

    @field_validator("args")
    @classmethod
    def validate_args(cls, value: List[str]) -> List[str]:
        if any(not isinstance(item, str) for item in value):
            raise ValueError("All command arguments must be strings")
        return value

    def to_request(self) -> CommandRequest:
        return CommandRequest(
            command=self.command,
            args=self.args,
            cwd=self.cwd,
            timeout=self.timeout,
        )


class GitActionPayload(BaseModel):
    action: str = Field(..., description="Git subcommand")
    args: List[str] = Field(default_factory=list)
    cwd: Optional[Path] = Field(default=None)
    timeout: Optional[float] = Field(default=None, ge=0)

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        if not value:
            raise ValueError("Git action is required")
        return value

    def to_request(self) -> GitActionRequest:
        return GitActionRequest(
            action=self.action,
            args=self.args,
            cwd=self.cwd,
            timeout=self.timeout,
        )


class TaskResponse(BaseModel):
    id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_task(cls, task: Task) -> "TaskResponse":
        payload: Dict[str, Any] = {
            "id": task.id,
            "status": task.status.value,
            "result": task.result,
            "error": task.error,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }
        return cls(**payload)


class TaskCreationResponse(BaseModel):
    id: str
    status: str


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]

    @classmethod
    def from_tasks(cls, tasks: List[Task]) -> "TaskListResponse":
        return cls(tasks=[TaskResponse.from_task(task) for task in tasks])


class KnowledgeQueryPayload(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=20)

    def to_request(self) -> KnowledgeQueryRequest:
        return KnowledgeQueryRequest(query=self.query, limit=self.limit)


class KnowledgeQueryResponse(BaseModel):
    results: List[Dict[str, Any]]


class SimulationPayload(BaseModel):
    outcomes: List[float]
    probabilities: List[float]
    runs: int = Field(default=100, ge=1, le=10_000)
    transition_matrix: Optional[Dict[str, Dict[str, float]]] = None
    initial_state: Optional[str] = None
    steps: Optional[int] = Field(default=None, ge=1, le=50)

    @field_validator("outcomes", "probabilities")
    @classmethod
    def validate_non_empty(cls, value: List[float]) -> List[float]:
        if not value:
            raise ValueError("List cannot be empty")
        return value

    def to_request(self) -> SimulationRequest:
        return SimulationRequest(
            outcomes=self.outcomes,
            probabilities=self.probabilities,
            runs=self.runs,
            transition_matrix=self.transition_matrix,
            initial_state=self.initial_state,
            steps=self.steps,
        )


class SimulationResponse(BaseModel):
    expectation: float
    samples: List[float]
    markov_path: Optional[List[str]] = None


class CursorPayload(BaseModel):
    prompt: str
    file_path: Optional[Path] = None
    apply_changes: bool = False
    extra_args: Dict[str, Any] = Field(default_factory=dict)

    def to_request(self) -> CursorInvocationRequest:
        return CursorInvocationRequest(
            prompt=self.prompt,
            file_path=self.file_path,
            apply_changes=self.apply_changes,
            extra_args=self.extra_args,
        )


class DashboardResponse(BaseModel):
    generated_at: datetime
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    knowledge_nodes: int
    knowledge_edges: int
    fairness_threshold: float
    dynamic_fairness: float
    collective_opt_in: bool
    plugins: List[Dict[str, Any]]

    @classmethod
    def from_snapshot(cls, snapshot: DashboardSnapshot) -> "DashboardResponse":
        return cls(
            generated_at=snapshot.generated_at,
            total_tasks=snapshot.total_tasks,
            completed_tasks=snapshot.completed_tasks,
            failed_tasks=snapshot.failed_tasks,
            knowledge_nodes=snapshot.knowledge_nodes,
            knowledge_edges=snapshot.knowledge_edges,
            fairness_threshold=snapshot.fairness_threshold,
            dynamic_fairness=snapshot.dynamic_fairness,
            collective_opt_in=snapshot.collective_opt_in,
            plugins=[
                {
                    "name": plugin.name,
                    "description": plugin.description,
                    "version": plugin.version,
                    "enabled": plugin.enabled,
                }
                for plugin in snapshot.active_plugins
            ],
        )


class PluginInfo(BaseModel):
    name: str
    description: str = ""
    version: str = "0.0.0"
    enabled: bool = True

    @classmethod
    def from_metadata(cls, metadata: PluginMetadata) -> "PluginInfo":
        return cls(
            name=metadata.name,
            description=metadata.description,
            version=metadata.version,
            enabled=metadata.enabled,
        )


class PluginListResponse(BaseModel):
    plugins: List[PluginInfo]

    @classmethod
    def from_metadata(cls, plugins: List[PluginMetadata]) -> "PluginListResponse":
        return cls(plugins=[PluginInfo.from_metadata(plugin) for plugin in plugins])


class PluginReloadResponse(PluginListResponse):
    status: str = "reloaded"


class PluginTogglePayload(BaseModel):
    name: str
    enabled: bool


class PluginToggleResponse(BaseModel):
    plugin: PluginInfo
    status: str


class HealthCheckSchema(BaseModel):
    name: str
    status: str
    detail: str = ""

    @classmethod
    def from_check(cls, check: HealthCheck) -> "HealthCheckSchema":
        return cls(name=check.name, status=check.status, detail=check.detail)


class HealthResponse(BaseModel):
    generated_at: datetime
    status: str
    checks: List[HealthCheckSchema]

    @classmethod
    def from_report(cls, report: HealthReport) -> "HealthResponse":
        return cls(
            generated_at=report.generated_at,
            status=report.status,
            checks=[HealthCheckSchema.from_check(check) for check in report.checks],
        )
