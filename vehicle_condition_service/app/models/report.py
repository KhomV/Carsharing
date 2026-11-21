from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReportPhase(str, Enum):
    BEFORE = "before"
    AFTER = "after"


class Photo(BaseModel):
    id: UUID
    content_type: str
    size_bytes: int


class ConditionReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phase: ReportPhase
    reference_id: UUID
    car_id: UUID
    created_at: datetime
    photos: list[Photo]
