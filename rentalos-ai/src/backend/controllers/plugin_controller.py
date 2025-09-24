"""Plugin endpoints reserved for Stage 3."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["plugins"])


@router.get("/plugins")
def list_plugins() -> dict:
    return {"plugins": []}
