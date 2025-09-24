"""
Cursor Auto-Invocation System
Automatically invokes Cursor IDE capabilities based on code changes and agent tasks.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

# Import Cursor client
from .cursor_client import CursorClient, AgentType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AutoInvocationRule:
    """Rule for automatic Cursor invocation."""

    trigger_pattern: str  # File pattern or event type
    agent_type: AgentType
    action: str
    priority: int = 1
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


class CursorAutoInvoker:
    """Automatically invokes Cursor capabilities based on triggers."""

    def __init__(self, cursor_client: CursorClient):
        self.cursor_client = cursor_client
        self.rules: List[AutoInvocationRule] = []
        self.is_running = False
        self.watch_paths: List[Path] = []

        # Setup default rules
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Setup default auto-invocation rules."""

        default_rules = [
            # Frontend changes trigger Frontend agent
            AutoInvocationRule(
                trigger_pattern="**/*.tsx",
                agent_type=AgentType.FRONTEND,
                action="generate_components",
                priority=1,
            ),
            AutoInvocationRule(
                trigger_pattern="**/*.jsx",
                agent_type=AgentType.FRONTEND,
                action="generate_components",
                priority=1,
            ),
            # Backend changes trigger Backend agent
            AutoInvocationRule(
                trigger_pattern="**/*.py",
                agent_type=AgentType.BACKEND,
                action="generate_apis",
                priority=1,
            ),
            AutoInvocationRule(
                trigger_pattern="**/api/**",
                agent_type=AgentType.BACKEND,
                action="generate_apis",
                priority=2,
            ),
            # CI/CD changes trigger CI/CD agent
            AutoInvocationRule(
                trigger_pattern="**/.github/workflows/**",
                agent_type=AgentType.CICD,
                action="optimize_pipeline",
                priority=1,
            ),
            AutoInvocationRule(
                trigger_pattern="**/Dockerfile",
                agent_type=AgentType.CICD,
                action="optimize_pipeline",
                priority=1,
            ),
            # Test files trigger QA agent
            AutoInvocationRule(
                trigger_pattern="**/test_*.py",
                agent_type=AgentType.QA,
                action="run_automated_reviews",
                priority=1,
            ),
            AutoInvocationRule(
                trigger_pattern="**/*.test.js",
                agent_type=AgentType.QA,
                action="run_automated_reviews",
                priority=1,
            ),
            # Architecture changes trigger Architect agent
            AutoInvocationRule(
                trigger_pattern="**/ARCHITECTURE.md",
                agent_type=AgentType.ARCHITECT,
                action="generate_blueprint",
                priority=1,
            ),
            AutoInvocationRule(
                trigger_pattern="**/src/**/__init__.py",
                agent_type=AgentType.ARCHITECT,
                action="generate_blueprint",
                priority=2,
            ),
            # Knowledge queries trigger Knowledge agent
            AutoInvocationRule(
                trigger_pattern="**/*.ndjson",
                agent_type=AgentType.KNOWLEDGE,
                action="traverse_brain_blocks",
                priority=1,
            ),
            AutoInvocationRule(
                trigger_pattern="**/docs/**",
                agent_type=AgentType.KNOWLEDGE,
                action="summarize_ndjson_scaffolds",
                priority=2,
            ),
        ]

        self.rules.extend(default_rules)
        logger.info(f"Setup {len(default_rules)} default auto-invocation rules")

    async def start_auto_invocation(self, watch_paths: List[Path]) -> None:
        """Start automatic Cursor invocation."""

        self.watch_paths = watch_paths
        self.is_running = True

        logger.info(f"Starting auto-invocation for {len(watch_paths)} paths")

        # Start watching for changes
        await self._watch_for_changes()

    async def _watch_for_changes(self) -> None:
        """Watch for file changes and trigger appropriate agents."""

        while self.is_running:
            try:
                # Check for file changes
                changed_files = await self._detect_changes()

                if changed_files:
                    await self._process_changes(changed_files)

                # Wait before next check
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in change detection: {e}")
                await asyncio.sleep(5)

    async def _detect_changes(self) -> List[Path]:
        """Detect changed files in watch paths."""

        changed_files = []

        for watch_path in self.watch_paths:
            if watch_path.exists():
                # Simple change detection based on file modification time
                for file_path in watch_path.rglob("*"):
                    if file_path.is_file():
                        # Check if file was modified recently (within last 5 seconds)
                        if time.time() - file_path.stat().st_mtime < 5:
                            changed_files.append(file_path)

        return changed_files

    async def _process_changes(self, changed_files: List[Path]) -> None:
        """Process file changes and trigger appropriate agents."""

        for file_path in changed_files:
            await self._trigger_agents_for_file(file_path)

    async def _trigger_agents_for_file(self, file_path: Path) -> None:
        """Trigger appropriate agents for a specific file."""

        file_str = str(file_path)

        for rule in self.rules:
            if not rule.enabled:
                continue

            # Check if file matches rule pattern
            if self._matches_pattern(file_str, rule.trigger_pattern):
                await self._execute_rule(rule, file_path)

    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if file path matches the pattern."""

        # Simple pattern matching (could be enhanced with proper glob matching)
        if "**" in pattern:
            # Handle recursive patterns
            base_pattern = pattern.replace("**", "").replace("*", "")
            return base_pattern in file_path
        elif "*" in pattern:
            # Handle single-level patterns
            import fnmatch

            return fnmatch.fnmatch(file_path, pattern)
        else:
            return pattern in file_path

    async def _execute_rule(self, rule: AutoInvocationRule, file_path: Path) -> None:
        """Execute an auto-invocation rule."""

        try:
            logger.info(f"Executing rule: {rule.agent_type.value} -> {rule.action} for {file_path}")

            # Get the appropriate agent
            agent = self.cursor_client.get_agent(rule.agent_type)

            # Prepare context for the agent
            context = {
                "file_path": str(file_path),
                "file_content": file_path.read_text(encoding="utf-8") if file_path.exists() else "",
                "trigger_rule": rule.trigger_pattern,
                "timestamp": datetime.now().isoformat(),
            }

            # Execute agent action based on rule
            result = await self._execute_agent_action(agent, rule.action, context)

            # Update rule statistics
            rule.last_triggered = datetime.now()
            rule.trigger_count += 1

            logger.info(f"Rule executed successfully: {result}")

        except Exception as e:
            logger.error(f"Error executing rule {rule.agent_type.value}: {e}")

    async def _execute_agent_action(self, agent, action: str, context: Dict[str, Any]) -> Any:
        """Execute a specific agent action."""

        if action == "generate_components":
            return await agent.generate_components(
                {
                    "componentType": "auto_generated",
                    "framework": "react",
                    "filePath": context["file_path"],
                    "content": context["file_content"],
                }
            )

        elif action == "generate_apis":
            return await agent.generate_apis(
                {
                    "apiType": "REST",
                    "framework": "fastapi",
                    "filePath": context["file_path"],
                    "content": context["file_content"],
                }
            )

        elif action == "optimize_pipeline":
            return await agent.optimize_pipeline(
                {
                    "pipelineType": "github_actions",
                    "filePath": context["file_path"],
                    "content": context["file_content"],
                }
            )

        elif action == "run_automated_reviews":
            return await agent.run_automated_reviews(
                context["file_content"],
                ["accessibility", "security", "performance", "code_quality"],
            )

        elif action == "generate_blueprint":
            return await agent.generate_blueprint(
                {
                    "requirements": ["Auto-generated architecture"],
                    "filePath": context["file_path"],
                    "content": context["file_content"],
                }
            )

        elif action == "traverse_brain_blocks":
            return await agent.traverse_brain_blocks(
                [],
                {
                    "query": f"Analyze file: {context['file_path']}",
                    "context": "file_analysis",
                    "content": context["file_content"],
                },
            )

        elif action == "summarize_ndjson_scaffolds":
            return await agent.summarize_ndjson_scaffolds(
                [],
                {
                    "outputFormat": "structured_knowledge",
                    "filePath": context["file_path"],
                    "content": context["file_content"],
                },
            )

        else:
            logger.warning(f"Unknown action: {action}")
            return None

    def add_rule(self, rule: AutoInvocationRule) -> None:
        """Add a new auto-invocation rule."""

        self.rules.append(rule)
        logger.info(f"Added new rule: {rule.agent_type.value} -> {rule.action}")

    def remove_rule(self, rule_index: int) -> None:
        """Remove an auto-invocation rule."""

        if 0 <= rule_index < len(self.rules):
            removed_rule = self.rules.pop(rule_index)
            logger.info(f"Removed rule: {removed_rule.agent_type.value} -> {removed_rule.action}")

    def get_rule_stats(self) -> Dict[str, Any]:
        """Get statistics about auto-invocation rules."""

        return {
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules if r.enabled]),
            "rules_by_agent": {
                agent_type.value: len([r for r in self.rules if r.agent_type == agent_type])
                for agent_type in AgentType
            },
            "total_triggers": sum(r.trigger_count for r in self.rules),
            "recent_triggers": [
                {
                    "agent": r.agent_type.value,
                    "action": r.action,
                    "last_triggered": r.last_triggered.isoformat() if r.last_triggered else None,
                    "trigger_count": r.trigger_count,
                }
                for r in self.rules
                if r.last_triggered
            ],
        }

    def stop_auto_invocation(self) -> None:
        """Stop automatic Cursor invocation."""

        self.is_running = False
        logger.info("Stopped auto-invocation")


# Global auto-invoker instance
_global_auto_invoker: Optional[CursorAutoInvoker] = None


def get_auto_invoker() -> CursorAutoInvoker:
    """Get the global auto-invoker instance."""
    global _global_auto_invoker
    if _global_auto_invoker is None:
        cursor_client = CursorClient()
        _global_auto_invoker = CursorAutoInvoker(cursor_client)
    return _global_auto_invoker


async def start_cursor_auto_invocation(watch_paths: List[Path]) -> None:
    """Start Cursor auto-invocation for specified paths."""

    auto_invoker = get_auto_invoker()
    await auto_invoker.start_auto_invocation(watch_paths)


# Export main classes and functions
__all__ = [
    "CursorAutoInvoker",
    "AutoInvocationRule",
    "get_auto_invoker",
    "start_cursor_auto_invocation",
]
