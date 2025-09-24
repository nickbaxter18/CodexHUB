"""Screening endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from ..services.screening_service import ScreeningResult, evaluate_applicant

router = APIRouter(tags=["screening"])


@router.post("/screening/evaluate", response_model=ScreeningResult)
async def evaluate(payload: Dict[str, Any]) -> ScreeningResult:
    return await evaluate_applicant(payload)
