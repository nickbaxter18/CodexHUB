"""Asset controller exposing CRUD endpoints."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter

from ..database.schema import AssetSchema

router = APIRouter(tags=["assets"])

_ASSETS = [
    AssetSchema(id=1, name="Smart Loft", location="Portland", esg_score=82.5),
    AssetSchema(id=2, name="Eco Villa", location="Austin", esg_score=88.1),
]


@router.get("/assets", response_model=List[AssetSchema])
def list_assets() -> List[AssetSchema]:
    return _ASSETS
