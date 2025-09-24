from datetime import datetime

import pytest

from src.backend.orchestrator.knowledge_base import knowledge_base
from src.backend.services.pricing_service import calculate_price, ingest_market_snapshot


@pytest.mark.asyncio
async def test_calculate_price_returns_components():
    knowledge_base.clear()
    result = await calculate_price(1, datetime.utcnow(), 7)
    assert result["asset_id"] == 1
    assert result["suggested_price"] > 0
    assert any(component["label"] == "base" for component in result["components"])


@pytest.mark.asyncio
async def test_calculate_price_respects_market_snapshot():
    knowledge_base.clear()
    ingest_market_snapshot(asset_id=2, rate=200.0, occupancy=0.95, esg_score=85.0, demand_index=1.2)
    ingest_market_snapshot(asset_id=2, rate=205.0, occupancy=0.96, esg_score=86.0, demand_index=1.1)
    result = await calculate_price(2, datetime.utcnow(), 7)
    assert result["suggested_price"] >= 200
    assert result["confidence"] >= 0.7
    component_labels = [component["label"] for component in result["components"]]
    assert "market_adjustment" in component_labels
