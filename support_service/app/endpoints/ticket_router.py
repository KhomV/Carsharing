from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.clients.source_client import current_account_id
from app.models.ticket import CreateMessage, CreateTicket, Ticket, TicketSummary
from app.services.support_service import SupportService


ticket_router = APIRouter(prefix="/support/tickets", tags=["Service support"])
bearer_scheme = HTTPBearer(auto_error=False)


def require_account_id(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> UUID:
    if credentials is None:
        raise HTTPException(
            status_code=401, detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_account_id(credentials.credentials)


@ticket_router.post("", response_model=Ticket, status_code=201)
def create_ticket(
    request: CreateTicket, account_id: UUID = Depends(require_account_id),
    service: SupportService = Depends(),
) -> Ticket:
    return service.create(account_id, request)


@ticket_router.get("", response_model=list[TicketSummary])
def list_tickets(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    account_id: UUID = Depends(require_account_id),
    service: SupportService = Depends(),
) -> list[TicketSummary]:
    return service.list(account_id, offset, limit)


@ticket_router.get("/{ticket_id}", response_model=Ticket)
def get_ticket(
    ticket_id: UUID, account_id: UUID = Depends(require_account_id),
    service: SupportService = Depends(),
) -> Ticket:
    return service.get(account_id, ticket_id)


@ticket_router.post("/{ticket_id}/messages", response_model=Ticket)
def add_message(
    ticket_id: UUID, request: CreateMessage, account_id: UUID = Depends(require_account_id),
    service: SupportService = Depends(),
) -> Ticket:
    return service.add_message(account_id, ticket_id, request)


@ticket_router.post("/{ticket_id}/close", response_model=Ticket)
def close_ticket(
    ticket_id: UUID, account_id: UUID = Depends(require_account_id),
    service: SupportService = Depends(),
) -> Ticket:
    return service.close(account_id, ticket_id)
