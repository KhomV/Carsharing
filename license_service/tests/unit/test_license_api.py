from unittest.mock import Mock
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.license_service import LicenseService
from app.settings import settings


@pytest.fixture
def api():
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize(("service_response", "expected"), [(401, 401), (502, 503)])
def test_submit_checks_bearer_with_auth_service(api, monkeypatch, service_response, expected):
    def get(url, *, headers, timeout):
        assert url.endswith("/api/auth/me")
        assert headers == {"Authorization": "Bearer test-token"}
        assert timeout > 0
        return httpx.Response(service_response, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", get)
    response = api.post(
        "/api/licenses",
        json={"series": "1234", "number": "567890", "expires_on": "2099-12-31"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == expected


def test_submit_requires_token(api):
    response = api.post(
        "/api/licenses", json={"series": "1234", "number": "567890", "expires_on": "2099-12-31"}
    )
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_invalid_document_number_is_not_echoed(api, monkeypatch):
    account_id = uuid4()

    def get(url, **_kwargs):
        return httpx.Response(200, json={"id": str(account_id)}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", get)
    response = api.post(
        "/api/licenses",
        json={"series": "1234", "number": "sensitive-input", "expires_on": "2099-12-31"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 422
    assert "sensitive-input" not in response.text


def test_status_requires_service_key(api):
    service = Mock(spec=LicenseService)
    service.get_status.return_value = {"status": "verified"}
    app.dependency_overrides[LicenseService] = lambda: service
    try:
        account_id = uuid4()
        path = f"/api/users/{account_id}/license-status"
        assert api.get(path).status_code == 401
        assert api.get(path, headers={"X-License-Status-Key": "incorrect"}).status_code == 401
        service.get_status.assert_not_called()

        response = api.get(path, headers={
            "X-License-Status-Key": settings.license_status_key.get_secret_value(),
        })
        assert response.status_code == 200
        assert response.json() == {"status": "verified"}
        service.get_status.assert_called_once_with(account_id)
    finally:
        app.dependency_overrides.pop(LicenseService)
