"""Community management service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Dict, List

from pydantic import BaseModel, Field

from ..utils.logger import get_logger
from ..utils.scheduling import add_minutes

logger = get_logger(__name__)

_COMMUNITY_EVENTS: Dict[int, List["CommunityEvent"]] = {}
_COMMUNITY_POSTS: Dict[int, List["CommunityPost"]] = {}


class CommunityEvent(BaseModel):
    id: int
    asset_id: int
    title: str
    scheduled_for: datetime
    capacity: int
    attendees: List[str] = Field(default_factory=list)


class CommunityPost(BaseModel):
    id: int
    asset_id: int
    author: str
    content: str
    created_at: datetime


def create_event(asset_id: int, title: str, minutes_from_now: int, capacity: int) -> CommunityEvent:
    events = _COMMUNITY_EVENTS.setdefault(asset_id, [])
    event = CommunityEvent(
        id=len(events) + 1,
        asset_id=asset_id,
        title=title,
        scheduled_for=add_minutes(datetime.now(UTC), minutes_from_now),
        capacity=capacity,
    )
    events.append(event)
    logger.info("Created community event", extra={"asset_id": asset_id, "title": title})
    return event


def join_event(asset_id: int, event_id: int, attendee: str) -> CommunityEvent:
    events = _COMMUNITY_EVENTS.get(asset_id, [])
    for event in events:
        if event.id == event_id:
            if attendee not in event.attendees and len(event.attendees) < event.capacity:
                event.attendees.append(attendee)
            return event
    raise ValueError("Event not found")


def list_events(asset_id: int) -> List[CommunityEvent]:
    return list(_COMMUNITY_EVENTS.get(asset_id, []))


def create_post(asset_id: int, author: str, content: str) -> CommunityPost:
    posts = _COMMUNITY_POSTS.setdefault(asset_id, [])
    post = CommunityPost(
        id=len(posts) + 1,
        asset_id=asset_id,
        author=author,
        content=content,
        created_at=datetime.now(UTC),
    )
    posts.append(post)
    return post


def get_feed(asset_id: int) -> List[CommunityPost]:
    return list(_COMMUNITY_POSTS.get(asset_id, []))
