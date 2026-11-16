from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CarStatus(str, Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    RENTED = "rented"
    MAINTENANCE = "maintenance"


class CreateCarRequest(BaseModel):
    model: str = Field(min_length=1)
    plate_number: str = Field(min_length=1)
    price_per_minute: int = Field(gt=0)


class Car(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    model: str
    plate_number: str
    status: CarStatus
    price_per_minute: int = Field(gt=0)
    created_at: datetime


class CarWithCoordinates(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    model: str
    plate_number: str
    status: CarStatus
    price_per_minute: int = Field(gt=0)
    latitude: float | None = None
    longitude: float | None = None
    fuel_level: int | None = None
    is_engine_on: bool | None = None
    is_handbrake_engaged: bool | None = None
