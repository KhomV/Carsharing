import pytest
from uuid import uuid4
from datetime import datetime, timezone
from telemetry_service.app.models.telemetry import Telemetry
from telemetry_service.app.repositories.db_telemetry_repo import TelemetryRepo


def test_telemetry_save_and_get_latest(db):
    """Тест 1: Запись телеметрии и чтение последних координат автомобиля."""
    repo = TelemetryRepo(db)
    car_id = uuid4()
    telemetry = Telemetry(
        id=uuid4(),
        car_id=car_id,
        latitude=55.751244,
        longitude=37.618423,
        fuel_level=85,
        mileage=12500,
        is_engine_on=True,
        is_handbrake_engaged=False,
        created_at=datetime.now(timezone.utc),
    )
    repo.create(telemetry)

    latest = repo.get_latest_by_car_id(car_id)
    assert latest is not None
    assert latest.id == telemetry.id
    assert latest.fuel_level == 85
    assert latest.latitude == 55.751244


def test_telemetry_history(db):
    """Тест 2: Сохранение двух записей и получение истории телеметрии."""
    repo = TelemetryRepo(db)
    car_id = uuid4()
    t1 = Telemetry(
        id=uuid4(),
        car_id=car_id,
        latitude=55.751244,
        longitude=37.618423,
        fuel_level=90,
        mileage=10000,
        is_engine_on=False,
        is_handbrake_engaged=True,
        created_at=datetime.now(timezone.utc),
    )
    t2 = t1.model_copy(update={"id": uuid4(), "fuel_level": 88, "mileage": 10020})

    repo.create(t1)
    repo.create(t2)

    history = repo.get_history(car_id)
    assert len(history) == 2
