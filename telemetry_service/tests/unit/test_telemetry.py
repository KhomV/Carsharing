from datetime import datetime, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.telemetry import RecordTelemetryRequest, Telemetry
from app.repositories.db_telemetry_repo import TelemetryRepo
from app.services.telemetry_service import TelemetryService


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def telemetry_data():
    return dict(
        id=uuid4(),
        car_id=uuid4(),
        latitude=55.7558,
        longitude=37.6173,
        fuel_level=85,
        mileage=12500,
        is_engine_on=False,
        is_handbrake_engaged=True,
        created_at=NOW,
    )


@pytest.fixture
def service():
    repo = Mock(spec=TelemetryRepo)
    repo.create.side_effect = lambda t: t
    repo.get_latest_by_car_id.return_value = None
    repo.get_latest_all_cars.return_value = []
    repo.get_history.return_value = []
    with patch("app.services.telemetry_service.TelemetryRepo", return_value=repo):
        yield TelemetryService(db=None), repo


def test_telemetry_model_valid(telemetry_data):
    telemetry = Telemetry(**telemetry_data)
    assert telemetry.fuel_level == 85
    assert telemetry.latitude == 55.7558
    assert telemetry.longitude == 37.6173


@pytest.mark.parametrize(
    "field,value",
    [
        ("latitude", 91.0),
        ("latitude", -91.0),
        ("longitude", 181.0),
        ("longitude", -181.0),
        ("fuel_level", -1),
        ("fuel_level", 101),
        ("mileage", -10),
    ],
)
def test_telemetry_model_invalid_ranges(telemetry_data, field, value):
    telemetry_data[field] = value
    with pytest.raises(ValidationError):
        Telemetry(**telemetry_data)


def test_record_telemetry_request_defaults():
    req = RecordTelemetryRequest(
        car_id=uuid4(),
        latitude=55.75,
        longitude=37.61,
        fuel_level=90,
        mileage=5000,
    )
    assert req.is_engine_on is False
    assert req.is_handbrake_engaged is True


def test_service_record_telemetry(service):
    app, repo = service
    car_id = uuid4()
    req = RecordTelemetryRequest(
        car_id=car_id,
        latitude=55.75,
        longitude=37.62,
        fuel_level=75,
        mileage=3400,
        is_engine_on=True,
        is_handbrake_engaged=False,
    )

    result = app.record_telemetry(req)
    assert result.car_id == car_id
    assert result.fuel_level == 75
    assert result.is_engine_on is True
    assert result.is_handbrake_engaged is False
    repo.create.assert_called_once_with(result)


def test_service_get_car_telemetry_found(service, telemetry_data):
    app, repo = service
    expected = Telemetry(**telemetry_data)
    repo.get_latest_by_car_id.return_value = expected

    result = app.get_car_telemetry(expected.car_id)
    assert result == expected
    repo.get_latest_by_car_id.assert_called_once_with(expected.car_id)


def test_service_get_car_telemetry_not_found(service):
    app, repo = service
    car_id = uuid4()
    with pytest.raises(KeyError, match="Телеметрия для автомобиля не найдена"):
        app.get_car_telemetry(car_id)


def test_service_get_all_cars_telemetry(service, telemetry_data):
    app, repo = service
    expected = [Telemetry(**telemetry_data)]
    repo.get_latest_all_cars.return_value = expected

    assert app.get_all_cars_telemetry() == expected
    repo.get_latest_all_cars.assert_called_once()
