from unittest.mock import Mock
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.main import app
from app.services.auth_service import AuthService
from app.services.security import hash_password, verify_password
from app.settings import settings


def test_password_hash_uses_random_salt():
    password = "test-passphrase"
    first = hash_password(password)
    assert first != hash_password(password)
    assert verify_password(password, first)
    assert not verify_password("wrong-password", first)


@pytest.fixture
def api():
    service = Mock(spec=AuthService)
    app.dependency_overrides[AuthService] = lambda: service
    try:
        with TestClient(app) as client:
            yield client, service
    finally:
        app.dependency_overrides.pop(AuthService)


def test_invalid_registration_does_not_echo_password(api):
    client, _ = api
    response = client.post("/api/auth/register", json={
        "email": "alice@example.test", "password": "secret", "full_name": "Alice",
    })
    assert response.status_code == 422
    assert "secret" not in response.text


def test_profile_requires_bearer_token(api):
    client, service = api
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    service.authenticate.assert_not_called()


@pytest.mark.parametrize(("status_code", "status", "expected"), [
    (200, "verified", (200, True, "verified")),
    (200, "pending", (200, False, "pending")),
    (200, "rejected", (200, False, "rejected")),
    (404, None, (200, False, "missing")),
    (200, "unknown", (503, None, None)),
    (500, None, (503, None, None)),
])
def test_eligibility_uses_license_service(api, monkeypatch, status_code, status, expected):
    client, service = api
    account_id = uuid4()
    service.authenticate.return_value.id = account_id

    monkeypatch.setattr(settings, "license_status_key", SecretStr("test-service-key"))

    def get(url, *, headers, timeout):
        assert url.endswith(f"/api/users/{account_id}/license-status")
        assert headers["X-License-Status-Key"] == "test-service-key"
        assert timeout > 0
        return httpx.Response(status_code, json={"status": status}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", get)
    response = client.get("/api/auth/me/eligibility", headers={"Authorization": "Bearer test-token"})
    service.authenticate.assert_called_once_with("test-token")
    assert response.status_code == expected[0]
    if response.is_success:
        assert response.json() == {"eligible": expected[1], "license_status": expected[2]}


def test_license_connection_failure_returns_503(api, monkeypatch):
    client, _ = api
    monkeypatch.setattr(httpx, "get", Mock(side_effect=httpx.ConnectError("offline")))
    response = client.get("/api/auth/me/eligibility", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 503
