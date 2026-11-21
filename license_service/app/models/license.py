from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LicenseState(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class SubmitLicense(BaseModel):
    model_config = ConfigDict(extra="forbid")

    series: str = Field(pattern=r"^[0-9]{4}$", repr=False)
    number: str = Field(pattern=r"^[0-9]{6}$", repr=False)
    expires_on: date


class LicenseStatus(BaseModel):
    status: LicenseState


class LicenseDetails(LicenseStatus):
    id: UUID
    expires_on: date
    number_last_four: str
    reason: str | None = None
