from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models.telemetry import Telemetry
from app.repositories.db_telemetry_repo import TelemetryRepo


@pytest.fixture
def telemetry():
    return Telemetry(
        id=uuid4(),
        car_id=uuid4(),
        latitude=55.751244,
        longitude=37.618423,
        fuel_level=92,
        mileage=8400,
        is_engine_on=False,
        is_handbrake_engaged=True,
        created_at=datetime.now(timezone.utc),
    )


def test_save_and_get_latest_telemetry(db, telemetry):
    repo = TelemetryRepo(db)
    repo.create(telemetry)
    db.expire_all()

    loaded = repo.get_latest_by_car_id(telemetry.car_id)
    assert loaded is not None
    assert loaded.id == telemetry.id
    assert loaded.car_id == telemetry.car_id
    assert loaded.fuel_level == telemetry.fuel_level
    assert loaded.latitude == telemetry.latitude
    assert loaded.longitude == telemetry.longitude


def test_missing_car_telemetry(db):
    repo = TelemetryRepo(db)
    assert repo.get_latest_by_car_id(uuid4()) is None


def test_get_latest_telemetry_after_updates(db, telemetry):
    repo = TelemetryRepo(db)
    repo.create(telemetry)

    newer = telemetry.model_copy(
        update={
            "id": uuid4(),
            "fuel_level": 88,
            "mileage": 8450,
            "created_at": datetime.now(timezone.utc),
        }
    )
    repo.create(newer)
    db.expire_all()

    latest = repo.get_latest_by_car_id(telemetry.car_id)
    assert latest is not None
    assert latest.id == newer.id
    assert latest.fuel_level == 88
    assert latest.mileage == 8450


def test_get_history(db, telemetry):
    repo = TelemetryRepo(db)
    repo.create(telemetry)

    second = telemetry.model_copy(
        update={
            "id": uuid4(),
            "created_at": datetime.now(timezone.utc),
        }
    )
    repo.create(second)

    history = repo.get_history(telemetry.car_id)
    assert len(history) == 2
    assert history[0].id == second.id
    assert history[1].id == telemetry.id
