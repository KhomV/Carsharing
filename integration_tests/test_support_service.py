import pytest
from uuid import uuid4
from datetime import datetime, timezone
from support_service.app.models.ticket import SupportTicket, TicketChannel, TicketCategory, TicketStatus


@pytest.fixture
def tickets_collection(mongo_db):
    """Возвращает коллекцию тикетов из изолированной тестовой БД Mongo."""
    return mongo_db["tickets"]


def test_ticket_create_and_find(tickets_collection):
    """Тест 1: Создание тикета техподдержки в MongoDB и получение по ID."""
    ticket_id = uuid4()
    account_id = uuid4()
    doc = {
        "_id": str(ticket_id),
        "account_id": str(account_id),
        "channel": TicketChannel.APP.value,
        "category": TicketCategory.GENERAL.value,
        "status": TicketStatus.OPEN.value,
        "subject": "Вопрос по приложению",
        "description": "Не могу найти кнопку",
        "rental_id": None,
        "car_id": None,
        "messages": [],
        "created_at": datetime.now(timezone.utc),
        "closed_at": None,
    }
    tickets_collection.insert_one(doc)

    found = tickets_collection.find_one({"_id": str(ticket_id)})
    assert found is not None
    assert found["account_id"] == str(account_id)
    assert found["status"] == "open"


def test_ticket_close_update(tickets_collection):
    """Тест 2: Добавление сообщения и закрытие обращения в MongoDB."""
    ticket_id = uuid4()
    account_id = uuid4()
    doc = {
        "_id": str(ticket_id),
        "account_id": str(account_id),
        "channel": TicketChannel.APP.value,
        "category": TicketCategory.GENERAL.value,
        "status": TicketStatus.OPEN.value,
        "subject": "Служба поддержки",
        "description": "Проблема решена",
        "rental_id": None,
        "car_id": None,
        "messages": [],
        "created_at": datetime.now(timezone.utc),
        "closed_at": None,
    }
    tickets_collection.insert_one(doc)

    # Закрываем тикет
    tickets_collection.update_one(
        {"_id": str(ticket_id)},
        {"$set": {"status": TicketStatus.CLOSED.value, "closed_at": datetime.now(timezone.utc)}},
    )

    updated = tickets_collection.find_one({"_id": str(ticket_id)})
    assert updated["status"] == "closed"
    assert updated["closed_at"] is not None
