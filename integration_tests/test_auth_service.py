import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from auth_service.app.repositories.db_account_repo import AccountRepo
from auth_service.app.schemas.account import AccountTable


def test_auth_create_account_and_find_by_email(db):
    """Тест 1: Регистрация аккаунта в БД и поиск по email."""
    repo = AccountRepo(db)
    email = f"user_{uuid4().hex[:8]}@example.com"
    account = repo.create_account(
        email=email,
        password_hash="hashed_secret_123",
        full_name="Иван Иванов",
    )

    found = repo.find_by_email(email)
    assert found is not None
    assert found.id == account.id
    assert found.full_name == "Иван Иванов"


def test_auth_create_and_validate_session(db):
    """Тест 2: Создание сессии с токеном и поиск аккаунта по сессии."""
    repo = AccountRepo(db)
    email = f"user_{uuid4().hex[:8]}@example.com"
    account = repo.create_account(
        email=email,
        password_hash="hashed_secret_123",
        full_name="Иван Иванов",
    )

    token_hash = f"token_hash_{uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    repo.create_session(account.id, token_hash, expires_at)

    session_account = repo.find_by_session(token_hash)
    assert session_account is not None
    assert session_account.id == account.id
