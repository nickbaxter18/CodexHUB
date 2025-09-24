"""Pydantic schemas mirroring the ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AssetSchema(BaseModel):
    id: int
    name: str
    location: str
    esg_score: float = Field(ge=0, le=100)

    model_config = ConfigDict(from_attributes=True)


class LeaseSchema(BaseModel):
    id: int
    asset_id: int
    tenant_name: str
    start_date: datetime
    end_date: datetime
    monthly_rent: float

    model_config = ConfigDict(from_attributes=True)


class PaymentSchema(BaseModel):
    id: int
    lease_id: int
    amount: float
    status: str
    due_date: datetime

    model_config = ConfigDict(from_attributes=True)


class ESGRecordSchema(BaseModel):
    id: int
    asset_id: int
    carbon_kg: float
    water_liters: float
    waste_kg: float
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventSchema(BaseModel):
    id: int
    title: str
    scheduled_for: datetime
    capacity: int

    model_config = ConfigDict(from_attributes=True)


class CommunitySchema(BaseModel):
    id: int
    asset_id: int
    name: str
    description: str
    events: Optional[List[EventSchema]] = None

    model_config = ConfigDict(from_attributes=True)
