"""UI helpers for rendering the Stage 3 dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..types import DashboardSnapshot

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
ENVIRONMENT = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_dashboard(snapshot: DashboardSnapshot) -> str:
    """Render the dashboard HTML using the provided snapshot."""

    template = ENVIRONMENT.get_template("index.html")
    context = _build_context(snapshot)
    return template.render(**context)


def _build_context(snapshot: DashboardSnapshot) -> Dict[str, object]:
    plugins = [
        {
            "name": metadata.name,
            "description": metadata.description,
            "version": metadata.version,
            "enabled": metadata.enabled,
        }
        for metadata in snapshot.active_plugins
    ]
    return {
        "generated_at": snapshot.generated_at.isoformat(),
        "total_tasks": snapshot.total_tasks,
        "completed_tasks": snapshot.completed_tasks,
        "failed_tasks": snapshot.failed_tasks,
        "knowledge_nodes": snapshot.knowledge_nodes,
        "knowledge_edges": snapshot.knowledge_edges,
        "fairness_threshold": snapshot.fairness_threshold,
        "dynamic_fairness": snapshot.dynamic_fairness,
        "collective_opt_in": snapshot.collective_opt_in,
        "plugins": plugins,
    }
