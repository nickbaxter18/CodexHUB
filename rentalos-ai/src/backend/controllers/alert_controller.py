"""Alert endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from ..services.alert_service import Alert, create_alert

router = APIRouter(tags=["alerts"])


@router.post("/alerts", response_model=Alert)
def create_alert_endpoint(payload: Dict[str, Any]) -> Alert:
    channel = str(payload.get("channel", "email"))
    message = str(payload.get("message", "Notification message"))
    metadata = payload.get("metadata") or {}
    return create_alert(channel, message, metadata)
