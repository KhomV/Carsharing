from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic import BaseModel, ConfigDict, Field


class InvoiceStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"


class Invoice(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    rental_id: UUID
    user_id: UUID
    amount: int = Field(gt=0)
    status: InvoiceStatus
    created_at: datetime
    paid_at: datetime | None = None