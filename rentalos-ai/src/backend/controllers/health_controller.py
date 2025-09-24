"""Resilience and observability endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from ..services.health_service import build_health_snapshot, readiness_probe

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    """Return a holistic health snapshot for dashboards."""

    return build_health_snapshot()


@router.get("/ready")
def ready() -> Dict[str, Any]:
    """Return readiness information suitable for load balancer probes."""

    snapshot = readiness_probe()
    if not snapshot.get("ready", False):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=snapshot)
    return snapshot
