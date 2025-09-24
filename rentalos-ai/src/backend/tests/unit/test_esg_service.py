import pytest

from src.backend.services.esg_service import compile_esg_report


@pytest.mark.asyncio
async def test_compile_esg_report_scores_metrics():
    report = await compile_esg_report(2, {"carbon_kg": 90, "water_liters": 700, "waste_kg": 20})
    assert report.asset_id == 2
    assert report.score >= 0
    assert any(metric.name == "carbon_intensity" for metric in report.metrics)
