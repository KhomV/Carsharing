from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RentalFinishedEvent(BaseModel):
    event_id: UUID
    rental_id: UUID
    user_id: UUID
    amount: int = Field(gt=0)
    finished_at: datetime