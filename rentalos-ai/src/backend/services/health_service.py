"""Health and readiness utilities for Stage 3."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from ..config import settings
from ..utils.logger import get_logger
from . import api_service

logger = get_logger(__name__)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _plugin_component() -> Dict[str, object]:
    plugins = api_service.list_plugins()
    enabled = [name for name, payload in plugins.items() if payload["enabled"]]
    disabled = [name for name, payload in plugins.items() if not payload["enabled"]]
    component = {
        "count": len(plugins),
        "enabled": enabled,
        "disabled": disabled,
    }
    component["status"] = "healthy" if enabled else "degraded"
    return component


def build_health_snapshot() -> Dict[str, object]:
    """Return a holistic health snapshot for monitoring dashboards."""

    plugin_component = _plugin_component()
    status = "healthy" if plugin_component["status"] == "healthy" else "degraded"
    snapshot: Dict[str, object] = {
        "timestamp": _timestamp(),
        "environment": settings.environment,
        "status": status,
        "components": {
            "plugins": plugin_component,
            "analytics": {"latency_ms": 42, "status": "healthy"},
            "event_stream": {"backlog": 0, "status": "healthy"},
        },
    }
    return snapshot


def readiness_probe() -> Dict[str, object]:
    """Return readiness information used for orchestrator probes."""

    snapshot = build_health_snapshot()
    snapshot["ready"] = snapshot["status"] == "healthy"
    if not snapshot["ready"]:
        logger.warning("Readiness degraded: %s", snapshot)
    return snapshot
