from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecordTelemetryRequest(BaseModel):
    car_id: UUID
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    fuel_level: int = Field(ge=0, le=100)
    mileage: int = Field(ge=0)
    is_engine_on: bool = False
    is_handbrake_engaged: bool = True


class Telemetry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    car_id: UUID
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    fuel_level: int = Field(ge=0, le=100)
    mileage: int = Field(ge=0)
    is_engine_on: bool
    is_handbrake_engaged: bool
    created_at: datetime
