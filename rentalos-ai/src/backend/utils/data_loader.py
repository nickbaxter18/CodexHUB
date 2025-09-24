"""Synthetic data loader for Stage 1."""

from __future__ import annotations

from datetime import datetime
from typing import Dict


def load_sensor_snapshot(asset_id: int) -> Dict[str, object]:
    base = 20 + asset_id
    return {
        "temperature": base + 2.1,
        "humidity": 45.0,
        "co2": 410.0,
        "timestamp": datetime.utcnow().isoformat(),
    }
