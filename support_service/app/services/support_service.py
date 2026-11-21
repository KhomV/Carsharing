from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, Request
from pymongo.collection import Collection

from app.clients.source_client import rental_car_id
from app.models.ticket import CreateMessage, CreateTicket, Message, Ticket, TicketStatus, TicketSummary
from app.repositories.ticket_repo import TicketRepo


def get_collection(request: Request) -> Collection:
    return request.app.state.tickets


def now() -> datetime:
    timestamp = datetime.now(timezone.utc)
    # BSON datetime stores milliseconds.
    return timestamp.replace(microsecond=timestamp.microsecond // 1000 * 1000)


class SupportService:
    def __init__(self, collection: Collection = Depends(get_collection)):
        self.repo = TicketRepo(collection)

    def create(self, account_id: UUID, request: CreateTicket) -> Ticket:
        car_id = rental_car_id(account_id, request.rental_id) if request.rental_id else None
        timestamp = now()
        ticket = Ticket(
            id=uuid4(), **request.model_dump(), car_id=car_id, status=TicketStatus.OPEN,
            created_at=timestamp, updated_at=timestamp, closed_at=None, messages=[],
        )
        self.repo.create(account_id, ticket)
        return ticket

    def get(self, account_id: UUID, ticket_id: UUID) -> Ticket:
        ticket = self.repo.find(account_id, ticket_id)
        if ticket is None:
            raise HTTPException(status_code=404, detail="Support ticket not found")
        return ticket

    def list(self, account_id: UUID, offset: int, limit: int) -> list[TicketSummary]:
        return self.repo.list(account_id, offset, limit)

    def add_message(self, account_id: UUID, ticket_id: UUID, request: CreateMessage) -> Ticket:
        message = Message(id=uuid4(), text=request.text, created_at=now())
        ticket = self.repo.add_message(account_id, ticket_id, message)
        if ticket is not None:
            return ticket
        ticket = self.get(account_id, ticket_id)
        detail = "Support ticket is closed" if ticket.status == TicketStatus.CLOSED else "Message limit reached"
        raise HTTPException(status_code=409, detail=detail)

    def close(self, account_id: UUID, ticket_id: UUID) -> Ticket:
        ticket = self.repo.close(account_id, ticket_id, now())
        return ticket if ticket is not None else self.get(account_id, ticket_id)
