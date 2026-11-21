from datetime import datetime
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, StringConstraints


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class Channel(str, Enum):
    CHAT = "chat"
    PHONE = "phone"


class Category(str, Enum):
    ACCIDENT = "accident"
    GENERAL = "general"


class TicketStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class CreateTicket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: Channel
    category: Category
    subject: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    description: NonEmptyText
    rental_id: UUID | None = None


class CreateMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: NonEmptyText


class Message(BaseModel):
    id: UUID
    text: str
    created_at: datetime


class TicketSummary(BaseModel):
    id: UUID = Field(validation_alias=AliasChoices("id", "_id"))
    channel: Channel
    category: Category
    subject: str
    rental_id: UUID | None
    car_id: UUID | None
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None


class Ticket(TicketSummary):
    description: str
    messages: list[Message]
