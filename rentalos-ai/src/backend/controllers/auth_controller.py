"""Authentication endpoints reserved for Stage 2."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["auth"])


@router.get("/auth/status")
def auth_status() -> dict:
    return {"status": "deferred", "detail": "Advanced authentication arrives in Stage 2."}
