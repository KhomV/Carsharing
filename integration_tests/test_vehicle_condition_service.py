import pytest
from uuid import uuid4
from datetime import datetime, timezone
from vehicle_condition_service.app.models.report import ReportPhase
from vehicle_condition_service.app.repositories.db_report_repo import ReportRepo


def test_report_create_and_find_by_reference(db):
    """Тест 1: Создание отчета об осмотре авто в БД и поиск по booking_id."""
    repo = ReportRepo(db)
    account_id = uuid4()
    booking_id = uuid4()
    car_id = uuid4()
    report_id = uuid4()

    row = repo.create_report(
        report_id=report_id,
        account_id=account_id,
        booking_id=booking_id,
        car_id=car_id,
        phase=ReportPhase.BEFORE,
    )
    repo.commit()

    found = repo.find_by_reference(ReportPhase.BEFORE, booking_id)
    assert found is not None
    assert found.id == report_id
    assert found.car_id == car_id
    assert found.phase == ReportPhase.BEFORE.value


def test_report_add_photo_attachment(db):
    """Тест 2: Прикрепление фотографии осмотра к отчету в БД."""
    repo = ReportRepo(db)
    report_id = uuid4()
    photo_id = uuid4()

    repo.create_report(
        report_id=report_id,
        account_id=uuid4(),
        booking_id=uuid4(),
        car_id=uuid4(),
        phase=ReportPhase.AFTER,
    )
    repo.commit()

    # Прикрепляем фото
    repo.add_photo(
        report_id=report_id,
        photo_id=photo_id,
        mime_type="image/jpeg",
        content_length=1024,
        storage_key=f"photos/{report_id}/{photo_id}.jpg",
    )
    repo.commit()

    photos = repo.list_photos(report_id)
    assert len(photos) == 1
    assert photos[0].id == photo_id
    assert photos[0].mime_type == "image/jpeg"
