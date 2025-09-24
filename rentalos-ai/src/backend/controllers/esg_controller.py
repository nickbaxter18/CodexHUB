"""ESG endpoints."""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter

from ..services.esg_service import ESGReport, compile_esg_report

router = APIRouter(tags=["esg"])


@router.post("/esg/report", response_model=ESGReport)
async def create_esg_report(payload: Dict[str, float]) -> ESGReport:
    asset_id = int(payload.get("asset_id", 1))
    return await compile_esg_report(asset_id, payload)
