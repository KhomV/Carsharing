from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.repositories.db_account_repo import AccountRepo
from app.services.security import token_digest


def test_register_then_login_with_postgres(db):
    email = f"{uuid4()}@example.test"
    payload = {"email": email.upper(), "password": "test-passphrase", "full_name": "Alice"}
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as client:
            registered = client.post("/api/auth/register", json=payload)
            assert registered.status_code == 201
            assert registered.json() == {
                "id": registered.json()["id"], "email": email, "full_name": "Alice",
            }
            assert client.post("/api/auth/register", json=payload).status_code == 409
            assert client.post("/api/auth/login", json={
                "email": email, "password": "incorrect",
            }).status_code == 401

            logged_in = client.post("/api/auth/login", json=payload)
            assert logged_in.status_code == 200
            assert logged_in.headers["Cache-Control"] == "no-store"
            token = logged_in.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            assert client.get("/api/auth/me", headers=headers).json() == registered.json()
            assert client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"}).status_code == 401

            repo = AccountRepo(db)
            account = repo.find_by_email(email)
            assert account.password_hash != payload["password"]
            repo.create_session(
                account.id, token_digest("expired"), datetime.now(timezone.utc) - timedelta(seconds=1),
            )
            assert client.get("/api/auth/me", headers={"Authorization": "Bearer expired"}).status_code == 401
    finally:
        app.dependency_overrides.pop(get_db)
