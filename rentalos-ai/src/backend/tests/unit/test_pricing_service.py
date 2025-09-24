from datetime import datetime

import pytest

from src.backend.services.pricing_service import calculate_price


@pytest.mark.asyncio
async def test_calculate_price_returns_components():
    result = await calculate_price(1, datetime.utcnow(), 7)
    assert result["asset_id"] == 1
    assert result["suggested_price"] > 0
    assert any(component["label"] == "base" for component in result["components"])
