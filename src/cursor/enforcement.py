"""
Cursor Integration Enforcement
Ensures 100% compliance with Cursor IDE integration requirements.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union
from functools import wraps
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CursorEnforcementError(Exception):
    """Raised when Cursor integration is not properly used."""

    pass


class CursorEnforcement:
    """Enforces Cursor IDE integration compliance."""

    def __init__(self):
        self.cursor_usage_log: List[Dict[str, Any]] = []
        self.enforcement_active = True
        self.required_agents = {
            ".tsx": "FRONTEND",
            ".jsx": "FRONTEND",
            ".py": "BACKEND",
            ".md": "ARCHITECT",
            "test": "QA",
            "workflow": "CICD",
            "pipeline": "CICD",
            ".ndjson": "KNOWLEDGE",
        }

    def log_cursor_usage(self, agent_type: str, action: str, file_path: str, success: bool):
        """Log Cursor usage for compliance tracking."""

        self.cursor_usage_log.append(
            {
                "timestamp": time.time(),
                "agent_type": agent_type,
                "action": action,
                "file_path": file_path,
                "success": success,
            }
        )

        logger.info(f"CURSOR USAGE: {agent_type} -> {action} for {file_path}")

    def determine_required_agent(self, file_path: str) -> str:
        """Determine required Cursor agent for file path."""

        file_path_lower = file_path.lower()

        for pattern, agent in self.required_agents.items():
            if pattern in file_path_lower:
                return agent

        return "META"  # Default to META agent

    def validate_cursor_usage(self, file_path: str, agent_type: str) -> bool:
        """Validate that Cursor integration is being used."""

        if not self.enforcement_active:
            return True

        # Check if this is a coding task
        if not self._is_coding_task(file_path):
            return True

        # Validate agent type matches file type
        required_agent = self.determine_required_agent(file_path)
        if agent_type != required_agent:
            raise CursorEnforcementError(
                f"Wrong agent type for {file_path}. Required: {required_agent}, Got: {agent_type}"
            )

        return True

    def _is_coding_task(self, file_path: str) -> bool:
        """Check if this is a coding task that requires Cursor integration."""

        coding_extensions = {".py", ".tsx", ".jsx", ".ts", ".js", ".md", ".yml", ".yaml"}
        file_ext = Path(file_path).suffix.lower()

        return file_ext in coding_extensions or "test" in file_path.lower()

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get Cursor usage statistics."""

        total_usage = len(self.cursor_usage_log)
        successful_usage = len([log for log in self.cursor_usage_log if log["success"]])
        agent_usage = {}

        for log in self.cursor_usage_log:
            agent = log["agent_type"]
            agent_usage[agent] = agent_usage.get(agent, 0) + 1

        return {
            "total_usage": total_usage,
            "successful_usage": successful_usage,
            "success_rate": successful_usage / total_usage if total_usage > 0 else 0,
            "agent_usage": agent_usage,
            "recent_usage": self.cursor_usage_log[-10:] if self.cursor_usage_log else [],
        }


# Global enforcement instance
_global_enforcement = CursorEnforcement()


def enforce_cursor_integration(agent_type: str, action: str):
    """Decorator to enforce Cursor integration for functions."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get file path from function context
            file_path = _get_file_path_from_context()

            # Validate Cursor usage
            _global_enforcement.validate_cursor_usage(file_path, agent_type)

            try:
                # Execute function
                result = await func(*args, **kwargs)

                # Log successful Cursor usage
                _global_enforcement.log_cursor_usage(agent_type, action, file_path, True)

                return result

            except Exception as e:
                # Log failed Cursor usage
                _global_enforcement.log_cursor_usage(agent_type, action, file_path, False)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Get file path from function context
            file_path = _get_file_path_from_context()

            # Validate Cursor usage
            _global_enforcement.validate_cursor_usage(file_path, agent_type)

            try:
                # Execute function
                result = func(*args, **kwargs)

                # Log successful Cursor usage
                _global_enforcement.log_cursor_usage(agent_type, action, file_path, True)

                return result

            except Exception as e:
                # Log failed Cursor usage
                _global_enforcement.log_cursor_usage(agent_type, action, file_path, False)
                raise

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def _get_file_path_from_context() -> str:
    """Get file path from current execution context."""

    # Try to get from frame
    frame = inspect.currentframe()
    try:
        # Walk up the call stack to find file path
        while frame:
            filename = frame.f_code.co_filename
            if filename and not filename.startswith("<"):
                return filename
            frame = frame.f_back
    finally:
        del frame

    return "unknown_file"


def require_cursor_agent(agent_type: str):
    """Require specific Cursor agent for function execution."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Validate agent type
            file_path = _get_file_path_from_context()
            _global_enforcement.validate_cursor_usage(file_path, agent_type)

            # Execute with Cursor agent
            return await _execute_with_cursor_agent(func, agent_type, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Validate agent type
            file_path = _get_file_path_from_context()
            _global_enforcement.validate_cursor_usage(file_path, agent_type)

            # Execute with Cursor agent
            return _execute_with_cursor_agent_sync(func, agent_type, *args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def _execute_with_cursor_agent(func: Callable, agent_type: str, *args, **kwargs):
    """Execute function with Cursor agent integration."""

    try:
        # Import Cursor client
        from .cursor_client import CursorClient, AgentType

        # Get Cursor client
        cursor_client = CursorClient()

        # Get appropriate agent
        agent = cursor_client.get_agent(AgentType(agent_type))

        # Prepare task payload
        task_payload = {
            "function": func.__name__,
            "args": args,
            "kwargs": kwargs,
            "agent_type": agent_type,
        }

        # Execute with agent
        result = await agent.perform_task(task_payload)

        # Log usage
        _global_enforcement.log_cursor_usage(
            agent_type, "execute_function", _get_file_path_from_context(), True
        )

        return result

    except Exception as e:
        _global_enforcement.log_cursor_usage(
            agent_type, "execute_function", _get_file_path_from_context(), False
        )
        raise CursorEnforcementError(f"Cursor agent execution failed: {e}")


def _execute_with_cursor_agent_sync(func: Callable, agent_type: str, *args, **kwargs):
    """Execute function with Cursor agent integration (sync version)."""

    try:
        # Import Cursor client
        from .cursor_client import CursorClient, AgentType

        # Get Cursor client
        cursor_client = CursorClient()

        # Get appropriate agent
        agent = cursor_client.get_agent(AgentType(agent_type))

        # Prepare task payload
        task_payload = {
            "function": func.__name__,
            "args": args,
            "kwargs": kwargs,
            "agent_type": agent_type,
        }

        # Execute with agent (sync)
        result = agent.perform_task_sync(task_payload)

        # Log usage
        _global_enforcement.log_cursor_usage(
            agent_type, "execute_function", _get_file_path_from_context(), True
        )

        return result

    except Exception as e:
        _global_enforcement.log_cursor_usage(
            agent_type, "execute_function", _get_file_path_from_context(), False
        )
        raise CursorEnforcementError(f"Cursor agent execution failed: {e}")


def validate_cursor_compliance() -> bool:
    """Validate that Cursor integration is being used properly."""

    stats = _global_enforcement.get_usage_stats()

    if stats["total_usage"] == 0:
        raise CursorEnforcementError("No Cursor integration usage detected!")

    if stats["success_rate"] < 0.8:
        raise CursorEnforcementError(
            f"Low Cursor integration success rate: {stats['success_rate']:.2%}"
        )

    return True


def get_cursor_usage_report() -> Dict[str, Any]:
    """Get comprehensive Cursor usage report."""

    stats = _global_enforcement.get_usage_stats()

    return {
        "enforcement_active": _global_enforcement.enforcement_active,
        "compliance_status": "COMPLIANT" if validate_cursor_compliance() else "NON_COMPLIANT",
        "usage_statistics": stats,
        "required_agents": _global_enforcement.required_agents,
        "recommendations": _generate_recommendations(stats),
    }


def _generate_recommendations(stats: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on usage statistics."""

    recommendations = []

    if stats["total_usage"] == 0:
        recommendations.append("Start using Cursor integration immediately!")

    if stats["success_rate"] < 0.9:
        recommendations.append("Improve Cursor integration success rate")

    if not stats["agent_usage"]:
        recommendations.append("Use more diverse Cursor agents")

    return recommendations


# Export main functions
__all__ = [
    "enforce_cursor_integration",
    "require_cursor_agent",
    "validate_cursor_compliance",
    "get_cursor_usage_report",
    "CursorEnforcementError",
]
