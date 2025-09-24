"""Orchestrator coordinating task execution."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..config import get_config
from ..decision import simulation
from ..execution import command_runner, cursor_adapter, git_actions, task_manager
from ..types import (
    CommandRequest,
    CursorInvocationRequest,
    DashboardSnapshot,
    GitActionRequest,
    HealthReport,
    KnowledgeQueryRequest,
    KnowledgeQueryResult,
    PluginMetadata,
    PluginOperationResult,
    SimulationRequest,
    SimulationResult,
    Task,
    TaskCreation,
    TaskList,
)
from ..ui import dashboard as dashboard_ui
from ..utils.logger import get_logger
from ..utils.observer import HealthObserver
from ..utils.plugin_loader import PluginLoader
from .collective_agent import CollectiveAgent
from .decision_agent import DecisionAgent
from .ethics_agent import EthicsAgent
from .knowledge_agent import KnowledgeAgent

LOGGER = get_logger("orchestrator")


class Orchestrator:
    """Stage 1 orchestrator coordinating agents and execution."""

    def __init__(
        self,
        manager: Optional[task_manager.TaskManager] = None,
        plugin_loader: Optional[PluginLoader] = None,
        observer: Optional[HealthObserver] = None,
    ) -> None:
        self.config = get_config()
        self.task_manager = manager or task_manager.DEFAULT_TASK_MANAGER
        self.knowledge_agent = KnowledgeAgent()
        self.decision_agent = DecisionAgent()
        self.collective_agent = CollectiveAgent()
        self.ethics_agent = EthicsAgent()
        self.plugin_loader = plugin_loader or PluginLoader(self.config.plugin_directory)
        self.observer = observer or HealthObserver(max_failures=self.config.max_task_failures)
        self.plugin_loader.load_plugins()
        self.observer.register_check("knowledge", self._health_check_knowledge)
        self.observer.register_check("plugins", self._health_check_plugins)
        self.observer.register_check("tasks", self._health_check_tasks)

    async def schedule_command(self, request: CommandRequest) -> TaskCreation:
        LOGGER.info("Scheduling command task")

        async def job() -> Dict[str, Any]:
            knowledge_context = await self.knowledge_agent.observe({"request": request})
            collective_context = await self.collective_agent.observe({"request": request})
            actions = [
                {"name": "execute", "expected_reward": 0.9, "weight": 0.7},
                {"name": "defer", "expected_reward": 0.3, "weight": 0.3},
            ]
            decision = await self.decision_agent.act({"actions": actions})
            ethics = await self.ethics_agent.act(
                {"risk": 0.1 if decision["selected_action"] == "execute" else 0.5}
            )
            if not ethics["approved"]:
                raise RuntimeError("Command rejected by ethics agent")
            try:
                result = await command_runner.run_command(request)
            except Exception:
                self.observer.record_failure("tasks")
                raise
            else:
                self.observer.record_success("tasks")
            await self.decision_agent.observe(
                {
                    "action": decision["selected_action"],
                    "outcome": 1 if result.return_code == 0 else -1,
                }
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.return_code,
                "started_at": result.started_at.isoformat(),
                "completed_at": result.completed_at.isoformat(),
                "knowledge": knowledge_context.get("suggestions", []),
                "collective": collective_context.get("signals", []),
                "decision": decision,
                "ethics": ethics,
            }

        return await self.task_manager.create_task(job)

    async def schedule_git_action(self, request: GitActionRequest) -> TaskCreation:
        LOGGER.info("Scheduling git action task")

        async def job() -> Dict[str, Any]:
            knowledge_context = await self.knowledge_agent.observe({"request": request})
            collective_context = await self.collective_agent.observe({"request": request})
            actions = [
                {"name": "execute_git", "expected_reward": 0.8, "weight": 0.6},
                {"name": "abort", "expected_reward": 0.2, "weight": 0.4},
            ]
            decision = await self.decision_agent.act({"actions": actions})
            ethics = await self.ethics_agent.act(
                {"risk": 0.15 if decision["selected_action"] == "execute_git" else 0.4}
            )
            if not ethics["approved"]:
                raise RuntimeError("Git action rejected by ethics agent")
            try:
                result = await git_actions.run_git_action(request)
            except Exception:
                self.observer.record_failure("tasks")
                raise
            else:
                self.observer.record_success("tasks")
            await self.decision_agent.observe(
                {
                    "action": decision["selected_action"],
                    "outcome": 1 if result.return_code == 0 else -1,
                }
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.return_code,
                "action": result.action,
                "started_at": result.started_at.isoformat(),
                "completed_at": result.completed_at.isoformat(),
                "knowledge": knowledge_context.get("suggestions", []),
                "collective": collective_context.get("signals", []),
                "decision": decision,
                "ethics": ethics,
            }

        return await self.task_manager.create_task(job)

    async def schedule_cursor_action(self, request: CursorInvocationRequest) -> TaskCreation:
        LOGGER.info("Scheduling cursor invocation")

        async def job() -> Dict[str, Any]:
            knowledge_context = await self.knowledge_agent.observe({"query": request.prompt})
            actions = [
                {"name": "generate", "expected_reward": 0.85, "weight": 0.7},
                {"name": "skip", "expected_reward": 0.25, "weight": 0.3},
            ]
            decision = await self.decision_agent.act({"actions": actions})
            ethics = await self.ethics_agent.act({"risk": 0.2 if request.apply_changes else 0.1})
            if not ethics["approved"]:
                raise RuntimeError("Cursor action rejected by ethics agent")
            try:
                result = await cursor_adapter.run_cursor(request)
            except Exception:
                self.observer.record_failure("tasks")
                raise
            else:
                self.observer.record_success("tasks")
            await self.decision_agent.observe(
                {
                    "action": decision["selected_action"],
                    "outcome": 1 if result.return_code == 0 else -1,
                }
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.return_code,
                "suggestions": result.suggestions,
                "knowledge": knowledge_context.get("suggestions", []),
                "decision": decision,
                "ethics": ethics,
            }

        return await self.task_manager.create_task(job)

    async def get_task(self, task_id: str) -> Optional[Task]:
        return await self.task_manager.get_task(task_id)

    async def list_tasks(self) -> TaskList:
        return await self.task_manager.list_tasks()

    async def query_knowledge(self, request: KnowledgeQueryRequest) -> KnowledgeQueryResult:
        response = await self.knowledge_agent.act(
            {"query": request.query, "limit": request.limit, "include_neighbours": True}
        )
        return KnowledgeQueryResult(results=response.get("results", []))

    async def run_simulation(self, request: SimulationRequest) -> SimulationResult:
        expectation = simulation.monte_carlo_expectation(
            request.outcomes,
            request.probabilities,
            runs=request.runs,
        )
        markov_path = None
        if request.transition_matrix and request.initial_state:
            steps = request.steps or 5
            markov_path = simulation.simulate_markov_chain(
                request.transition_matrix,
                request.initial_state,
                steps=steps,
            )
        samples = simulation.run_batched_simulation(
            lambda _: request.outcomes, runs=min(request.runs, 10)
        )
        return SimulationResult(
            expectation=expectation,
            samples=[float(value) for value in samples],
            markov_path=markov_path,
        )

    async def dashboard_snapshot(self) -> DashboardSnapshot:
        tasks = await self.task_manager.list_tasks()
        total = len(tasks.tasks)
        completed = sum(1 for task in tasks.tasks if task.status.value == "completed")
        failed = sum(1 for task in tasks.tasks if task.status.value == "failed")
        knowledge_stats = self.knowledge_agent.stats()
        ethics_stats = self.ethics_agent.stats()
        plugins = self.plugin_loader.list_plugins()
        return DashboardSnapshot(
            generated_at=datetime.now(timezone.utc),
            total_tasks=total,
            completed_tasks=completed,
            failed_tasks=failed,
            active_plugins=plugins,
            knowledge_nodes=int(knowledge_stats.get("nodes", 0)),
            knowledge_edges=int(knowledge_stats.get("edges", 0)),
            fairness_threshold=float(ethics_stats.get("fairness_threshold", 0.0)),
            dynamic_fairness=float(ethics_stats.get("dynamic_threshold", 0.0)),
            collective_opt_in=bool(self.collective_agent.metrics().get("opt_in", False)),
        )

    async def render_dashboard(self) -> str:
        snapshot = await self.dashboard_snapshot()
        return dashboard_ui.render_dashboard(snapshot)

    def list_plugins(self) -> List[PluginMetadata]:
        return self.plugin_loader.list_plugins()

    async def reload_plugins(self) -> List[PluginMetadata]:
        return self.plugin_loader.reload()

    def toggle_plugin(self, name: str, enabled: bool) -> PluginOperationResult:
        metadata = self.plugin_loader.set_enabled(name, enabled)
        status = "enabled" if metadata.enabled else "disabled"
        return PluginOperationResult(name=metadata.name, status=status)

    async def health_report(self) -> HealthReport:
        return await self.observer.run_checks()

    def _health_check_knowledge(self) -> Dict[str, str]:
        try:
            stats = self.knowledge_agent.stats()
        except Exception as exc:  # noqa: BLE001
            return {"status": "unhealthy", "detail": str(exc)}
        if stats.get("nodes", 0) == 0:
            return {"status": "degraded", "detail": "knowledge graph empty"}
        return {"status": "healthy", "detail": f"nodes={stats['nodes']}"}

    def _health_check_plugins(self) -> Dict[str, str]:
        plugins = self.plugin_loader.list_plugins()
        detail = f"plugins={len(plugins)}"
        status = "healthy" if plugins or not self.config.plugin_directory.exists() else "degraded"
        return {"status": status, "detail": detail}

    def _health_check_tasks(self) -> Dict[str, str]:
        failures = self.observer.failure_counts().get("tasks", 0)
        if failures >= self.config.max_task_failures:
            return {"status": "unhealthy", "detail": f"task failures={failures}"}
        if failures:
            return {"status": "degraded", "detail": f"task failures={failures}"}
        return {"status": "healthy", "detail": "task queue stable"}
