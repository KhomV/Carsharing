from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID

from app.schemas.base_schema import Base


class TelemetryTable(Base):
    __tablename__ = "car_telemetry"

    id = Column(UUID(as_uuid=True), primary_key=True)
    car_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    fuel_level = Column(Integer, nullable=False)
    mileage = Column(Integer, nullable=False)
    is_engine_on = Column(Boolean, nullable=False, default=False)
    is_handbrake_engaged = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "latitude >= -90.0 AND latitude <= 90.0",
            name="ck_telemetry_latitude",
        ),
        CheckConstraint(
            "longitude >= -180.0 AND longitude <= 180.0",
            name="ck_telemetry_longitude",
        ),
        CheckConstraint(
            "fuel_level >= 0 AND fuel_level <= 100",
            name="ck_telemetry_fuel_level",
        ),
        CheckConstraint(
            "mileage >= 0",
            name="ck_telemetry_mileage",
        ),
        Index(
            "ix_car_telemetry_car_created",
            "car_id",
            created_at.desc(),
        ),
    )
