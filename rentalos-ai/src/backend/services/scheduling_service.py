"""Scheduling service for tasks and vendor coordination."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Iterable, List

from pydantic import BaseModel

from ..orchestrator import dispatcher
from ..utils.logger import get_logger
from ..utils.scheduling import add_minutes

logger = get_logger(__name__)


class ScheduleEntry(BaseModel):
    id: int
    title: str
    scheduled_for: datetime
    priority: int


async def build_schedule(items: Iterable[dict]) -> List[ScheduleEntry]:
    payload_items = list(items)
    agent_result = await dispatcher.dispatch("scheduling", {"items": payload_items})
    ordered = agent_result["data"]["ordered"]
    now = datetime.now(UTC)
    entries = []
    for idx, item in enumerate(ordered, start=1):
        entries.append(
            ScheduleEntry(
                id=idx,
                title=item.get("title", f"Task {idx}"),
                scheduled_for=add_minutes(now, idx * 30),
                priority=item.get("priority", 5),
            )
        )
    logger.debug("Built schedule", extra={"count": len(entries)})
    return entries
