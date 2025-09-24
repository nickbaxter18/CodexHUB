"""Alert service delivering notifications."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Dict, List

from pydantic import BaseModel

from ..utils.logger import get_logger

logger = get_logger(__name__)

_ALERTS: List["Alert"] = []


class Alert(BaseModel):
    id: int
    channel: str
    message: str
    created_at: datetime
    metadata: Dict[str, str]


def create_alert(channel: str, message: str, metadata: Dict[str, str] | None = None) -> Alert:
    alert = Alert(
        id=len(_ALERTS) + 1,
        channel=channel,
        message=message,
        created_at=datetime.now(UTC),
        metadata=metadata or {},
    )
    _ALERTS.append(alert)
    logger.info("Created alert", extra={"channel": channel})
    return alert


def list_alerts() -> List[Alert]:
    return list(_ALERTS)
