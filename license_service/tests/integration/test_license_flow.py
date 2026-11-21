from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import get_db
from app.endpoints.license_router import current_account_id
from app.main import app
from app.repositories.db_license_repo import LicenseRepo
from app.settings import settings


def test_license_lifecycle(db):
    account_id = uuid4()
    active_account_id = account_id
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[current_account_id] = lambda: active_account_id
    today = datetime.now(timezone.utc).date()
    future = (today + timedelta(days=30)).isoformat()
    past = (today - timedelta(days=1)).isoformat()

    try:
        with TestClient(app) as client:
            status_path = f"/api/users/{account_id}/license-status"
            service_headers = {"X-License-Status-Key": settings.license_status_key.get_secret_value()}
            assert client.get(status_path, headers=service_headers).status_code == 404

            document = {"series": "0123", "number": "456789", "expires_on": future}
            submitted = client.post("/api/licenses", json=document)
            assert submitted.status_code == 201
            assert submitted.json() == {
                "id": submitted.json()["id"], "status": "pending", "expires_on": future,
                "number_last_four": "6789", "reason": None,
            }
            assert client.get(status_path, headers=service_headers).json() == {"status": "pending"}

            verify_path = f"/api/licenses/{submitted.json()['id']}/verify"
            active_account_id = uuid4()
            assert client.post(verify_path).status_code == 404

            active_account_id = account_id
            verified = client.post(verify_path)
            assert verified.status_code == 200
            assert verified.json()["status"] == "verified"
            assert client.get(status_path, headers=service_headers).json() == {"status": "verified"}

            repo = LicenseRepo(db)
            row = repo.find_by_account(account_id)
            row.expires_on = today - timedelta(days=1)
            repo.commit()
            assert client.get(status_path, headers=service_headers).json() == {"status": "rejected"}

            document["expires_on"] = past
            replacement = client.post("/api/licenses", json=document)
            assert replacement.status_code == 201
            assert replacement.json()["id"] != submitted.json()["id"]
            assert client.get(status_path, headers=service_headers).json() == {"status": "pending"}
            assert client.post(verify_path).status_code == 404
            rejected = client.post(f"/api/licenses/{replacement.json()['id']}/verify")
            assert rejected.status_code == 200
            assert rejected.json()["status"] == "rejected"
            assert rejected.json()["reason"] == "expired"
            assert client.get(status_path, headers=service_headers).json() == {"status": "rejected"}
    finally:
        app.dependency_overrides.pop(get_db)
        app.dependency_overrides.pop(current_account_id)
