from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic import BaseModel, ConfigDict, Field


class RentalStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    FINISHED = "finished"


class CreateRentalRequest(BaseModel):
    user_id: UUID
    car_id: UUID


class Rental(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    car_id: UUID
    status: RentalStatus
    started_at: datetime
    finished_at: datetime | None = None
    price_per_minute: int = Field(gt=0)
    total_amount: int | None = Field(default=None, ge=0)