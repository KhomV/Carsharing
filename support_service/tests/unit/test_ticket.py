from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.clients import source_client
from app.main import app
from app.services.support_service import SupportService


@pytest.fixture
def api():
    app.dependency_overrides[SupportService] = lambda: object()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(SupportService)


def test_requires_bearer_token(api):
    response = api.get("/api/support/tickets")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(("upstream_status", "expected"), [(401, 401), (500, 503)])
def test_authentication_errors(api, monkeypatch, upstream_status, expected):
    def fetch(url, *, headers):
        assert url.endswith("/api/auth/me")
        assert headers == {"Authorization": "Bearer test-token"}
        return httpx.Response(upstream_status, request=httpx.Request("GET", url))

    monkeypatch.setattr(source_client, "fetch", fetch)
    assert api.get("/api/support/tickets", headers={"Authorization": "Bearer test-token"}).status_code == expected


def test_whitespace_description_is_invalid(api, monkeypatch):
    def fetch(url, **_kwargs):
        return httpx.Response(200, request=httpx.Request("GET", url), json={"id": str(uuid4())})

    monkeypatch.setattr(source_client, "fetch", fetch)
    response = api.post("/api/support/tickets", headers={"Authorization": "Bearer test-token"}, json={
        "channel": "chat", "category": "general", "subject": "Request", "description": "   ",
    })
    assert response.status_code == 422


@pytest.mark.parametrize("is_owner", [True, False])
def test_rental_is_scoped_to_account(monkeypatch, is_owner):
    account_id, rental_id, car_id = uuid4(), uuid4(), uuid4()

    def fetch(url):
        assert url.endswith(f"/api/rentals/{rental_id}")
        return httpx.Response(200, request=httpx.Request("GET", url), json={
            "user_id": str(account_id if is_owner else uuid4()),
            "car_id": str(car_id),
        })

    monkeypatch.setattr(source_client, "fetch", fetch)
    if is_owner:
        assert source_client.rental_car_id(account_id, rental_id) == car_id
    else:
        with pytest.raises(HTTPException) as error:
            source_client.rental_car_id(account_id, rental_id)
        assert error.value.status_code == 404
