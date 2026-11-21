from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, field_validator


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
    created_at: AwareDatetime
    photos: list[Photo]

    @field_validator("created_at")
    @classmethod
    def normalize_created_at(cls, value: datetime) -> datetime:
        return value.astimezone(timezone.utc)
