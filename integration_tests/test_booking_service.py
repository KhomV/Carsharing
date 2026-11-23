import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from booking_service.app.models.car import Car, CarStatus
from booking_service.app.models.booking import Booking, BookingStatus
from booking_service.app.repositories.db_car_repo import CarRepo
from booking_service.app.repositories.db_booking_repo import BookingRepo


def test_car_create_and_get(db):
    """Тест 1: Добавление автомобиля в БД и получение по ID."""
    repo = CarRepo(db)
    car = Car(
        id=uuid4(),
        model="Skoda Octavia",
        plate_number="A123BC777",
        status=CarStatus.AVAILABLE,
        price_per_minute=1500,
        created_at=datetime.now(timezone.utc),
    )
    repo.create(car)

    found = repo.get_by_id(car.id)
    assert found is not None
    assert found.plate_number == "A123BC777"
    assert found.status == CarStatus.AVAILABLE


def test_booking_create_and_find_active(db):
    """Тест 2: Создание бронирования и поиск активной брони по автомобилю."""
    car_repo = CarRepo(db)
    car = Car(
        id=uuid4(),
        model="Kia Rio",
        plate_number="B456CD777",
        status=CarStatus.AVAILABLE,
        price_per_minute=1200,
        created_at=datetime.now(timezone.utc),
    )
    car_repo.create(car)

    booking_repo = BookingRepo(db)
    now = datetime.now(timezone.utc)
    booking = Booking(
        id=uuid4(),
        car_id=car.id,
        user_id=uuid4(),
        status=BookingStatus.ACTIVE,
        created_at=now,
        expires_at=now + timedelta(minutes=20),
    )
    booking_repo.create(booking)

    active = booking_repo.get_active_by_car_id(car.id)
    assert active is not None
    assert active.id == booking.id
    assert active.status == BookingStatus.ACTIVE
