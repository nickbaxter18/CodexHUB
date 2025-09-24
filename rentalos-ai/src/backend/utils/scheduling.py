"""Scheduling helpers."""

from __future__ import annotations

from datetime import datetime, timedelta


def add_minutes(moment: datetime, minutes: int) -> datetime:
    return moment + timedelta(minutes=minutes)
