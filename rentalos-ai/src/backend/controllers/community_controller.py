"""Community endpoints."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from ..services.community_service import (
    CommunityEvent,
    CommunityPost,
    create_event,
    create_post,
    join_event,
    list_events,
)

router = APIRouter(tags=["community"])


@router.post("/community/events", response_model=CommunityEvent)
def create_community_event(payload: Dict[str, Any]) -> CommunityEvent:
    asset_id = int(payload.get("asset_id", 1))
    title = str(payload.get("title", "Community Gathering"))
    minutes = int(payload.get("minutes_from_now", 60))
    capacity = int(payload.get("capacity", 25))
    return create_event(asset_id, title, minutes, capacity)


@router.post("/community/events/{event_id}/join", response_model=CommunityEvent)
def join_community_event(event_id: int, payload: Dict[str, Any]) -> CommunityEvent:
    asset_id = int(payload.get("asset_id", 1))
    attendee = str(payload.get("attendee", "Guest"))
    return join_event(asset_id, event_id, attendee)


@router.get("/community/events", response_model=List[CommunityEvent])
def list_community_events(asset_id: int = 1) -> List[CommunityEvent]:
    return list_events(asset_id)


@router.post("/community/posts", response_model=CommunityPost)
def create_community_post(payload: Dict[str, Any]) -> CommunityPost:
    asset_id = int(payload.get("asset_id", 1))
    author = str(payload.get("author", "Manager"))
    content = str(payload.get("content", "Welcome to the community!"))
    return create_post(asset_id, author, content)
