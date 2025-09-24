"""SQLAlchemy models representing core entities."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Numeric, String, Table
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp for ORM defaults."""

    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    assets = relationship("Asset", back_populates="owner")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    esg_score = Column(Float, default=0.0)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="assets")
    leases = relationship("Lease", back_populates="asset")


class Lease(Base):
    __tablename__ = "leases"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"))
    tenant_name = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    monthly_rent = Column(Numeric, nullable=False)

    asset = relationship("Asset", back_populates="leases")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    lease_id = Column(Integer, ForeignKey("leases.id"))
    amount = Column(Numeric, nullable=False)
    status = Column(String, nullable=False)
    due_date = Column(DateTime, nullable=False)


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"))
    sensor_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=utcnow)


class ESGRecord(Base):
    __tablename__ = "esg_records"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"))
    carbon_kg = Column(Float, nullable=False)
    water_liters = Column(Float, nullable=False)
    waste_kg = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=utcnow)


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"))
    holder = Column(String, nullable=False)
    shares = Column(Float, nullable=False)
    issued_at = Column(DateTime, default=utcnow)


class Community(Base):
    __tablename__ = "communities"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"))
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    community_id = Column(Integer, ForeignKey("communities.id"))
    title = Column(String, nullable=False)
    scheduled_for = Column(DateTime, nullable=False)
    capacity = Column(Integer, nullable=False)


class EventBooking(Base):
    __tablename__ = "event_bookings"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    attendee = Column(String, nullable=False)
    status = Column(String, default="confirmed")


asset_tags = Table(
    "asset_tags",
    Base.metadata,
    Column("asset_id", Integer, ForeignKey("assets.id")),
    Column("tag", String, nullable=False),
)
