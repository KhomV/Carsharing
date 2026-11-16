from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BookingStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class CreateBookingRequest(BaseModel):
    user_id: UUID
    car_id: UUID
    duration_minutes: int = Field(default=20, gt=0, le=120)


class Booking(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    car_id: UUID
    user_id: UUID
    status: BookingStatus
    created_at: datetime
    expires_at: datetime
    cancelled_at: datetime | None = None
