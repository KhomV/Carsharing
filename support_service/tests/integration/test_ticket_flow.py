import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database import connect_mongo, prepare_tickets
from app.endpoints.ticket_router import require_account_id
from app.main import app
from app.services import support_service
from app.settings import settings


@pytest.fixture
def mongo(monkeypatch):
    if os.getenv("ALLOW_TEST_DATABASE") != "1" or not settings.mongo_database.endswith("_test"):
        pytest.fail("Use only an explicitly enabled isolated *_test database")
    monkeypatch.setattr(settings, "mongo_database", f"{uuid4().hex}_test")
    with connect_mongo() as client:
        collection = prepare_tickets(client)
        try:
            yield collection
        finally:
            client.drop_database(settings.mongo_database)


def test_accident_ticket_lifecycle_and_owner_scope(mongo, monkeypatch):
    account_id, rental_id, car_id = uuid4(), uuid4(), uuid4()
    viewer = account_id

    def linked_car(owner, requested_rental):
        assert owner == account_id
        assert requested_rental == rental_id
        return car_id

    monkeypatch.setattr(support_service, "rental_car_id", linked_car)
    app.dependency_overrides[require_account_id] = lambda: viewer
    app.dependency_overrides[support_service.get_collection] = lambda: mongo
    try:
        with TestClient(app) as client:
            path = "/api/support/tickets"
            response = client.post(path, json={
                "channel": "phone", "category": "accident",
                "subject": "Accident", "description": "Damage recorded",
                "rental_id": str(rental_id),
            })
            assert response.status_code == 201
            ticket = response.json()
            assert ticket["rental_id"] == str(rental_id)
            assert ticket["car_id"] == str(car_id)
            assert ticket["status"] == "open"
            assert ticket["messages"] == []
            ticket_path = f"{path}/{ticket['id']}"
            assert client.get(ticket_path).json() == ticket
            assert client.get(path).json()[0]["id"] == ticket["id"]
            assert "messages" not in client.get(path).json()[0]
            assert client.get(f"{path}?offset=1&limit=1").json() == []

            viewer = uuid4()
            assert client.get(path).json() == []
            assert client.get(ticket_path).status_code == 404
            assert client.post(ticket_path + "/messages", json={"text": "Foreign"}).status_code == 404
            assert client.post(ticket_path + "/close").status_code == 404

            viewer = account_id
            with ThreadPoolExecutor(max_workers=4) as pool:
                responses = list(pool.map(
                    lambda text: client.post(ticket_path + "/messages", json={"text": text}),
                    ("First", "Second", "Third", "Fourth"),
                ))
            assert all(result.status_code == 200 for result in responses)
            updated = client.get(ticket_path).json()
            assert {message["text"] for message in updated["messages"]} == {
                "First", "Second", "Third", "Fourth",
            }
            closed = client.post(ticket_path + "/close").json()
            assert closed["status"] == "closed"
            assert closed["closed_at"] is not None
            assert client.post(ticket_path + "/close").json() == closed
            assert client.post(ticket_path + "/messages", json={"text": "Too late"}).status_code == 409
    finally:
        app.dependency_overrides.clear()
