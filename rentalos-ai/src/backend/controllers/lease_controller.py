"""Lease endpoints."""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter

from ..services.lease_service import LeaseSummary, abstract_lease

router = APIRouter(tags=["leases"])


@router.post("/leases/abstract", response_model=LeaseSummary)
async def abstract(payload: Dict[str, str]) -> LeaseSummary:
    document = payload.get("document", "")
    return await abstract_lease(document)
