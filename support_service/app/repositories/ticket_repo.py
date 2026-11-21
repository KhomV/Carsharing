from datetime import datetime
from uuid import UUID

from pymongo import ReturnDocument
from pymongo.collection import Collection

from app.models.ticket import Message, Ticket, TicketStatus, TicketSummary


MAX_MESSAGES = 100


class TicketRepo:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, account_id: UUID, ticket: Ticket) -> None:
        document = ticket.model_dump()
        document["_id"] = document.pop("id")
        document["account_id"] = account_id
        self.collection.insert_one(document)

    def find(self, account_id: UUID, ticket_id: UUID) -> Ticket | None:
        document = self.collection.find_one({"_id": ticket_id, "account_id": account_id})
        return Ticket.model_validate(document) if document is not None else None

    def list(self, account_id: UUID, offset: int, limit: int) -> list[TicketSummary]:
        documents = (
            self.collection.find({"account_id": account_id}, {"description": 0, "messages": 0})
            .sort([("created_at", -1), ("_id", -1)])
            .skip(offset)
            .limit(limit)
        )
        return [TicketSummary.model_validate(document) for document in documents]

    def add_message(self, account_id: UUID, ticket_id: UUID, message: Message) -> Ticket | None:
        document = self.collection.find_one_and_update(
            {
                "_id": ticket_id,
                "account_id": account_id,
                "status": TicketStatus.OPEN.value,
                f"messages.{MAX_MESSAGES - 1}": {"$exists": False},
            },
            {
                "$push": {"messages": message.model_dump()},
                "$max": {"updated_at": message.created_at},
            },
            return_document=ReturnDocument.AFTER,
        )
        return Ticket.model_validate(document) if document is not None else None

    def close(self, account_id: UUID, ticket_id: UUID, closed_at: datetime) -> Ticket | None:
        document = self.collection.find_one_and_update(
            {"_id": ticket_id, "account_id": account_id, "status": TicketStatus.OPEN.value},
            {
                "$set": {"status": TicketStatus.CLOSED.value, "closed_at": closed_at},
                "$max": {"updated_at": closed_at},
            },
            return_document=ReturnDocument.AFTER,
        )
        return Ticket.model_validate(document) if document is not None else None
