import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from license_service.app.models.license import LicenseStatus
from license_service.app.repositories.db_license_repo import LicenseRepo


def test_license_create_and_find_by_account(db):
    """Тест 1: Сохранение водительского удостоверения в БД."""
    repo = LicenseRepo(db)
    account_id = uuid4()
    license_id = uuid4()
    today = datetime.now(timezone.utc).date()
    expires_on = today + timedelta(days=365)

    row = repo.create_or_replace(
        license_id=license_id,
        account_id=account_id,
        series="1234",
        number_last_four="5678",
        number_hash="hash_value_123",
        expires_on=expires_on,
        status=LicenseStatus.PENDING,
        reason=None,
    )
    repo.commit()

    found = repo.find_by_account(account_id)
    assert found is not None
    assert found.id == license_id
    assert found.status == LicenseStatus.PENDING
    assert found.number_last_four == "5678"


def test_license_verify_update(db):
    """Тест 2: Подтверждение (верификация) водительского удостоверения."""
    repo = LicenseRepo(db)
    account_id = uuid4()
    license_id = uuid4()
    today = datetime.now(timezone.utc).date()

    repo.create_or_replace(
        license_id=license_id,
        account_id=account_id,
        series="1234",
        number_last_four="5678",
        number_hash="hash_value_123",
        expires_on=today + timedelta(days=365),
        status=LicenseStatus.PENDING,
        reason=None,
    )
    repo.commit()

    # Верифицируем права
    row = repo.find_by_id(license_id)
    row.status = LicenseStatus.VERIFIED
    repo.commit()

    updated = repo.find_by_account(account_id)
    assert updated.status == LicenseStatus.VERIFIED
