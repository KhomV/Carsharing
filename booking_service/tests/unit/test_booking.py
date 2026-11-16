from datetime import datetime, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.clients.telemetry_client import TelemetryClient
from app.models.booking import Booking, BookingStatus, CreateBookingRequest
from app.models.car import Car, CarStatus, CreateCarRequest
from app.repositories.db_booking_repo import BookingRepo
from app.repositories.db_car_repo import CarRepo
from app.services.booking_service import BookingService


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def car_data():
    return dict(
        id=uuid4(),
        model="Kia Rio",
        plate_number="A123BC777",
        status=CarStatus.AVAILABLE,
        price_per_minute=1500,
        created_at=NOW,
    )


@pytest.fixture
def service():
    car_repo = Mock(spec=CarRepo)
    car_repo.create.side_effect = lambda c: c
    car_repo.update_status.side_effect = lambda cid, st: None
    car_repo.get_by_id.return_value = None
    car_repo.get_available.return_value = []
    car_repo.get_all.return_value = []

    booking_repo = Mock(spec=BookingRepo)
    booking_repo.create.side_effect = lambda b: b
    booking_repo.update.side_effect = lambda b: b
    booking_repo.get_active_by_user_id.return_value = None
    booking_repo.get_active_by_car_id.return_value = None
    booking_repo.get_by_id.return_value = None
    booking_repo.get_all.return_value = []

    telemetry_client = Mock(spec=TelemetryClient)
    telemetry_client.get_car_telemetry.return_value = None
    telemetry_client.get_all_cars_telemetry.return_value = {}

    with (
        patch("app.services.booking_service.CarRepo", return_value=car_repo),
        patch("app.services.booking_service.BookingRepo", return_value=booking_repo),
    ):
        svc = BookingService(db=None, telemetry_client=telemetry_client)
        yield svc, car_repo, booking_repo, telemetry_client


def test_car_model_valid(car_data):
    car = Car(**car_data)
    assert car.model == "Kia Rio"
    assert car.status == CarStatus.AVAILABLE


def test_car_model_invalid_price(car_data):
    car_data["price_per_minute"] = 0
    with pytest.raises(ValidationError):
        Car(**car_data)


def test_create_car(service):
    app, car_repo, _, _ = service
    req = CreateCarRequest(
        model="Haval Jolion",
        plate_number="B777BB777",
        price_per_minute=1800,
    )
    result = app.create_car(req)
    assert result.model == "Haval Jolion"
    assert result.plate_number == "B777BB777"
    assert result.status == CarStatus.AVAILABLE
    car_repo.create.assert_called_once()


def test_get_available_cars_on_map_with_telemetry(service, car_data):
    app, car_repo, _, telemetry_client = service
    car = Car(**car_data)
    car_repo.get_available.return_value = [car]

    telemetry_client.get_all_cars_telemetry.return_value = {
        car.id: {
            "car_id": str(car.id),
            "latitude": 55.75,
            "longitude": 37.61,
            "fuel_level": 95,
            "is_engine_on": False,
            "is_handbrake_engaged": True,
        }
    }

    result = app.get_available_cars_on_map()
    assert len(result) == 1
    car_map = result[0]
    assert car_map.id == car.id
    assert car_map.latitude == 55.75
    assert car_map.longitude == 37.61
    assert car_map.fuel_level == 95


def test_create_booking_success(service, car_data):
    app, car_repo, booking_repo, _ = service
    car = Car(**car_data)
    car_repo.get_by_id.return_value = car

    user_id = uuid4()
    req = CreateBookingRequest(user_id=user_id, car_id=car.id, duration_minutes=20)
    booking = app.create_booking(req)

    assert booking.car_id == car.id
    assert booking.user_id == user_id
    assert booking.status == BookingStatus.ACTIVE
    booking_repo.create.assert_called_once()
    car_repo.update_status.assert_called_once_with(car.id, CarStatus.BOOKED)


def test_create_booking_unavailable_car(service, car_data):
    app, car_repo, booking_repo, _ = service
    car_data["status"] = CarStatus.RENTED
    car = Car(**car_data)
    car_repo.get_by_id.return_value = car

    req = CreateBookingRequest(user_id=uuid4(), car_id=car.id)
    with pytest.raises(ValueError, match="недоступен для бронирования"):
        app.create_booking(req)
    booking_repo.create.assert_not_called()


def test_cancel_booking(service, car_data):
    app, car_repo, booking_repo, _ = service
    booking = Booking(
        id=uuid4(),
        car_id=car_data["id"],
        user_id=uuid4(),
        status=BookingStatus.ACTIVE,
        created_at=NOW,
        expires_at=NOW,
    )
    booking_repo.get_by_id.return_value = booking

    cancelled = app.cancel_booking(booking.id)
    assert cancelled.status == BookingStatus.CANCELLED
    assert cancelled.cancelled_at is not None
    booking_repo.update.assert_called_once()
    car_repo.update_status.assert_called_once_with(booking.car_id, CarStatus.AVAILABLE)
