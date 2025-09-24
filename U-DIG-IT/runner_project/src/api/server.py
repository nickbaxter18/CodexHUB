"""FastAPI server exposing the runner API."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from ..agents.orchestrator import Orchestrator
from .schemas import (
    CommandPayload,
    CursorPayload,
    DashboardResponse,
    GitActionPayload,
    HealthResponse,
    KnowledgeQueryPayload,
    KnowledgeQueryResponse,
    PluginInfo,
    PluginListResponse,
    PluginReloadResponse,
    PluginTogglePayload,
    PluginToggleResponse,
    SimulationPayload,
    SimulationResponse,
    TaskCreationResponse,
    TaskListResponse,
    TaskResponse,
)

app = FastAPI(title="Probabilistic Multi-Agent Runner", version="0.1.0")
ORCHESTRATOR = Orchestrator()


@app.post("/run-command", response_model=TaskCreationResponse)
async def run_command(payload: CommandPayload) -> TaskCreationResponse:
    creation = await ORCHESTRATOR.schedule_command(payload.to_request())
    return TaskCreationResponse(id=creation.task_id, status=creation.status.value)


@app.post("/git-action", response_model=TaskCreationResponse)
async def git_action(payload: GitActionPayload) -> TaskCreationResponse:
    creation = await ORCHESTRATOR.schedule_git_action(payload.to_request())
    return TaskCreationResponse(id=creation.task_id, status=creation.status.value)


@app.post("/cursor-run", response_model=TaskCreationResponse)
async def cursor_run(payload: CursorPayload) -> TaskCreationResponse:
    creation = await ORCHESTRATOR.schedule_cursor_action(payload.to_request())
    return TaskCreationResponse(id=creation.task_id, status=creation.status.value)


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str) -> TaskResponse:
    task = await ORCHESTRATOR.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.from_task(task)


@app.get("/tasks", response_model=TaskListResponse)
async def list_tasks() -> TaskListResponse:
    tasks = await ORCHESTRATOR.list_tasks()
    return TaskListResponse.from_tasks(tasks.tasks)


@app.post("/knowledge/query", response_model=KnowledgeQueryResponse)
async def knowledge_query(payload: KnowledgeQueryPayload) -> KnowledgeQueryResponse:
    result = await ORCHESTRATOR.query_knowledge(payload.to_request())
    return KnowledgeQueryResponse(results=result.results)


@app.post("/simulate", response_model=SimulationResponse)
async def run_simulation(payload: SimulationPayload) -> SimulationResponse:
    result = await ORCHESTRATOR.run_simulation(payload.to_request())
    return SimulationResponse(
        expectation=result.expectation,
        samples=result.samples,
        markov_path=result.markov_path,
    )


@app.get("/dashboard/overview", response_model=DashboardResponse)
async def dashboard_overview() -> DashboardResponse:
    snapshot = await ORCHESTRATOR.dashboard_snapshot()
    return DashboardResponse.from_snapshot(snapshot)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page() -> HTMLResponse:
    html = await ORCHESTRATOR.render_dashboard()
    return HTMLResponse(content=html)


@app.get("/plugins", response_model=PluginListResponse)
async def list_plugins() -> PluginListResponse:
    plugins = ORCHESTRATOR.list_plugins()
    return PluginListResponse.from_metadata(plugins)


@app.post("/plugins/reload", response_model=PluginReloadResponse)
async def reload_plugins() -> PluginReloadResponse:
    plugins = await ORCHESTRATOR.reload_plugins()
    infos = [PluginInfo.from_metadata(plugin) for plugin in plugins]
    return PluginReloadResponse(plugins=infos)


@app.post("/plugins/toggle", response_model=PluginToggleResponse)
async def toggle_plugin(payload: PluginTogglePayload) -> PluginToggleResponse:
    result = ORCHESTRATOR.toggle_plugin(payload.name, payload.enabled)
    plugin_metadata = ORCHESTRATOR.list_plugins()
    plugin = next((item for item in plugin_metadata if item.name == result.name), None)
    info = (
        PluginInfo.from_metadata(plugin)
        if plugin
        else PluginInfo(name=result.name, enabled=payload.enabled)
    )
    return PluginToggleResponse(plugin=info, status=result.status)


@app.get("/health", response_model=HealthResponse)
async def health_status() -> HealthResponse:
    report = await ORCHESTRATOR.health_report()
    return HealthResponse.from_report(report)
