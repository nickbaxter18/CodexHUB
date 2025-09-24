import pytest

from src.backend.orchestrator.knowledge_base import knowledge_base
from src.backend.services.maintenance_service import (
    SensorWindow,
    detect_anomalies,
    generate_schedule,
)


@pytest.mark.asyncio
async def test_generate_schedule_creates_tasks():
    knowledge_base.clear()
    tasks = await generate_schedule(1)
    assert len(tasks) == 2
    assert tasks[0].asset_id == 1


def test_detect_anomalies_flags_large_deviation():
    knowledge_base.clear()
    baseline_window = SensorWindow(metric="temperature", samples=[70, 71, 69])
    detect_anomalies([baseline_window])  # establish baseline
    anomalous = SensorWindow(metric="temperature", samples=[80, 81, 82])
    scores = detect_anomalies([anomalous])
    assert "temperature" in scores
    assert scores["temperature"] >= 2


@pytest.mark.asyncio
async def test_generate_schedule_includes_anomaly_task():
    knowledge_base.clear()
    baseline = SensorWindow(metric="pressure", samples=[29, 30, 31])
    anomalous = SensorWindow(metric="pressure", samples=[30, 31, 46])
    tasks = await generate_schedule(2, sensor_windows=[baseline, anomalous])
    descriptions = [task.description for task in tasks]
    assert any("pressure" in desc for desc in descriptions)
