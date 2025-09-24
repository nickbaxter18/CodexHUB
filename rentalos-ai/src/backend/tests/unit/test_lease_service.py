import pytest

from src.backend.services.lease_service import abstract_lease


@pytest.mark.asyncio
async def test_abstract_lease_returns_summary():
    summary = await abstract_lease("Lease document")
    assert summary.monthly_rent == 1895.0
    assert len(summary.clauses) >= 2
