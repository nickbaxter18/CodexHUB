"""Energy utility helpers."""

from __future__ import annotations


def carbon_intensity(carbon_kg: float, energy_kwh: float) -> float:
    if energy_kwh <= 0:
        return 0.0
    return round(carbon_kg / energy_kwh, 3)
