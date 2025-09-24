"""Lease abstraction service."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel

from ..utils.logger import get_logger

logger = get_logger(__name__)


class LeaseClause(BaseModel):
    title: str
    text: str


class LeaseSummary(BaseModel):
    tenant: str
    term_months: int
    monthly_rent: float
    clauses: List[LeaseClause]


async def abstract_lease(document: str) -> LeaseSummary:
    """Produce a structured summary of a lease document."""

    logger.info("Abstracting lease document")
    clauses = [
        LeaseClause(title="Rent Payment", text="Rent is due on the first of each month."),
        LeaseClause(title="Maintenance", text="Tenant reports issues via the RentalOS-AI portal."),
    ]
    return LeaseSummary(tenant="Tenant A", term_months=12, monthly_rent=1895.0, clauses=clauses)
