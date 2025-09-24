"""
Cursor Auto-Invocation System
Automatically invokes Cursor IDE capabilities based on code changes and agent tasks.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import Cursor client
from .cursor_client import AgentType, CursorClient

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())


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
        self._watch_task: Optional[asyncio.Task[None]] = None
        self.mode = self._resolve_mode()
        if not self.cursor_client.enabled and self.mode != "manual":
            logger.info("Cursor client disabled; forcing auto-invocation manual mode")
            self.mode = "manual"
        self.poll_interval = self._resolve_poll_interval()
        self.ignored_directories = {
            ".git",
            "node_modules",
            "__pycache__",
            "cache",
        }
        self._file_mtimes: Dict[Path, float] = {}

        # Setup default rules
        self._setup_default_rules()
        self.file_patterns = self._resolve_file_patterns()

        if self.mode == "manual":
            logger.info("Cursor auto-invoker configured for manual mode; file watching disabled")
            self.poll_interval = None

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

        if self.mode == "minimal":
            minimal_patterns = {
                "**/*.py",
                "**/*.ts",
                "**/*.tsx",
                "**/*.js",
            }
            default_rules = [
                rule for rule in default_rules if rule.trigger_pattern in minimal_patterns
            ]
            logger.info(
                "Cursor auto-invoker running in minimal mode; %s rules enabled",
                len(default_rules),
            )
        elif self.mode == "manual":
            for rule in default_rules:
                rule.enabled = False
            logger.info("Cursor auto-invoker rules loaded in manual mode (all disabled)")

        self.rules.extend(default_rules)
        logger.info(f"Setup {len(default_rules)} default auto-invocation rules")

    async def start_auto_invocation(self, watch_paths: List[Path]) -> None:
        """Start automatic Cursor invocation."""

        if self.is_running:
            logger.info("Cursor auto-invoker already running")
            return

        self.watch_paths = watch_paths

        logger.info(f"Starting auto-invocation for {len(watch_paths)} paths")

        if self.mode == "manual":
            logger.info("Manual mode active; skipping file watcher start")
            return

        self.is_running = True

        await self._prime_file_snapshot()

        if self.poll_interval:
            loop = asyncio.get_running_loop()
            self._watch_task = loop.create_task(
                self._watch_for_changes(),
                name="cursor-auto-invocation-watch",
            )
        else:
            logger.info("Cursor auto-invocation started without file watcher (interval disabled)")

    async def _watch_for_changes(self) -> None:
        """Watch for file changes and trigger appropriate agents."""

        while self.is_running:
            try:
                # Check for file changes
                changed_files = await self._detect_changes()

                if changed_files:
                    await self._process_changes(changed_files)

                # Wait before next check
                await asyncio.sleep(self.poll_interval or 5)

            except Exception as e:
                logger.error(f"Error in change detection: {e}")
                await asyncio.sleep(5)

    async def _detect_changes(self) -> List[Path]:
        """Detect changed files in watch paths."""

        changed_files = []

        for watch_path in self.watch_paths:
            if not watch_path.exists():
                continue

            for pattern in self.file_patterns:
                for file_path in watch_path.glob(pattern):
                    if not file_path.is_file():
                        continue
                    if any(part in self.ignored_directories for part in file_path.parts):
                        continue

                    mtime = file_path.stat().st_mtime
                    previous = self._file_mtimes.get(file_path)
                    self._file_mtimes[file_path] = mtime

                    if previous is None:
                        continue

                    if mtime > previous:
                        changed_files.append(file_path)

        for tracked_file in list(self._file_mtimes.keys()):
            if not tracked_file.exists():
                self._file_mtimes.pop(tracked_file, None)

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
            if agent is None:
                logger.debug(
                    "Skipping rule %s for %s; Cursor client disabled",
                    rule.action,
                    rule.agent_type.value,
                )
                return

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

    async def _execute_agent_action(self, agent: Any, action: str, context: Dict[str, Any]) -> Any:
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

        if not self.is_running:
            return

        self.is_running = False
        if self._watch_task and not self._watch_task.done():
            self._watch_task.cancel()
        self._watch_task = None
        logger.info("Stopped auto-invocation")

    def _resolve_file_patterns(self) -> List[str]:
        env_patterns = os.getenv("CURSOR_FILE_PATTERNS")
        if env_patterns:
            patterns = [pattern.strip() for pattern in env_patterns.split(",") if pattern.strip()]
            if self.mode == "minimal":
                patterns = [
                    pattern
                    for pattern in patterns
                    if any(ext in pattern for ext in (".py", ".ts", ".tsx", ".js"))
                ]
            return patterns

        if self.mode == "manual":
            return []

        return sorted({rule.trigger_pattern for rule in self.rules if rule.enabled})

    def _resolve_mode(self) -> str:
        raw_value = os.getenv("CURSOR_AUTO_INVOCATION_MODE", "full").strip().lower()
        if raw_value not in {"full", "minimal", "manual"}:
            logger.warning(
                "Unknown CURSOR_AUTO_INVOCATION_MODE '%s'; defaulting to 'full'",
                raw_value,
            )
            return "full"
        return raw_value

    def _resolve_poll_interval(self) -> Optional[int]:
        raw_value = os.getenv("CURSOR_MONITOR_INTERVAL")
        if raw_value is None:
            return 5

        try:
            interval = int(raw_value)
        except ValueError:
            logger.warning(
                "Invalid CURSOR_MONITOR_INTERVAL '%s'; using default 5 seconds",
                raw_value,
            )
            return 5

        return interval if interval > 0 else None

    async def _prime_file_snapshot(self) -> None:
        for watch_path in self.watch_paths:
            if not watch_path.exists():
                continue
            for pattern in self.file_patterns:
                for file_path in watch_path.glob(pattern):
                    if file_path.is_file() and not any(
                        part in self.ignored_directories for part in file_path.parts
                    ):
                        self._file_mtimes[file_path] = file_path.stat().st_mtime


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

    if os.getenv("CURSOR_AUTO_INVOCATION_ENABLED", "true").lower() in {"0", "false", "off"}:
        logger.info("Cursor auto-invocation disabled via CURSOR_AUTO_INVOCATION_ENABLED")
        return

    auto_invoker = get_auto_invoker()
    if not auto_invoker.cursor_client.enabled:
        logger.info("Cursor client disabled; skipping auto-invocation startup")
        return
    await auto_invoker.start_auto_invocation(watch_paths)


# Export main classes and functions
__all__ = [
    "CursorAutoInvoker",
    "AutoInvocationRule",
    "get_auto_invoker",
    "start_cursor_auto_invocation",
]
