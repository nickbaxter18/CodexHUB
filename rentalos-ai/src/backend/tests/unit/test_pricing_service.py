from datetime import UTC, datetime

import pytest

from src.backend.orchestrator.knowledge_base import knowledge_base
from src.backend.services import api_service
from src.backend.services.pricing_service import calculate_price, ingest_market_snapshot


@pytest.mark.asyncio
async def test_calculate_price_returns_components():
    knowledge_base.clear()
    api_service.registry = api_service.PluginRegistry()
    api_service._auto_load_attempted = False
    api_service.reload_default_plugins()
    ingest_market_snapshot(
        asset_id=1,
        rate=185.0,
        occupancy=0.97,
        esg_score=88.0,
        demand_index=1.05,
    )
    result = await calculate_price(1, datetime.now(UTC), 21)
    assert result["asset_id"] == 1
    assert result["suggested_price"] > 0
    assert any(component["label"] == "base" for component in result["components"])
    assert any(
        component["label"].startswith("equitable-pricing") for component in result["components"]
    )


@pytest.mark.asyncio
async def test_calculate_price_respects_market_snapshot():
    knowledge_base.clear()
    ingest_market_snapshot(asset_id=2, rate=200.0, occupancy=0.95, esg_score=85.0, demand_index=1.2)
    ingest_market_snapshot(asset_id=2, rate=205.0, occupancy=0.96, esg_score=86.0, demand_index=1.1)
    result = await calculate_price(2, datetime.now(UTC), 7)
    assert result["suggested_price"] >= 200
    assert result["confidence"] >= 0.7
    component_labels = [component["label"] for component in result["components"]]
    assert "market_adjustment" in component_labels
