from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.models.booking import Booking, BookingStatus
from app.models.car import Car, CarStatus
from app.repositories.db_booking_repo import BookingRepo
from app.repositories.db_car_repo import CarRepo


@pytest.fixture
def car():
    return Car(
        id=uuid4(),
        model="Skoda Octavia",
        plate_number="X123XX777",
        status=CarStatus.AVAILABLE,
        price_per_minute=1600,
        created_at=datetime.now(timezone.utc),
    )


def test_create_and_find_car(db, car):
    repo = CarRepo(db)
    repo.create(car)
    db.expire_all()

    found = repo.get_by_id(car.id)
    assert found.id == car.id
    assert found.plate_number == car.plate_number
    assert found.status == CarStatus.AVAILABLE


def test_unique_plate_number(db, car):
    repo = CarRepo(db)
    repo.create(car)
    duplicate = car.model_copy(update={"id": uuid4()})
    with pytest.raises(ValueError, match="госномером уже существует"):
        repo.create(duplicate)


def test_create_and_find_booking(db, car):
    car_repo = CarRepo(db)
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
    db.expire_all()

    found = booking_repo.get_by_id(booking.id)
    assert found.id == booking.id
    assert found.status == BookingStatus.ACTIVE

    active = booking_repo.get_active_by_car_id(car.id)
    assert active is not None
    assert active.id == booking.id


def test_cannot_have_two_active_bookings_for_same_car(db, car):
    CarRepo(db).create(car)
    booking_repo = BookingRepo(db)
    now = datetime.now(timezone.utc)
    b1 = Booking(
        id=uuid4(),
        car_id=car.id,
        user_id=uuid4(),
        status=BookingStatus.ACTIVE,
        created_at=now,
        expires_at=now + timedelta(minutes=20),
    )
    booking_repo.create(b1)

    b2 = Booking(
        id=uuid4(),
        car_id=car.id,
        user_id=uuid4(),
        status=BookingStatus.ACTIVE,
        created_at=now,
        expires_at=now + timedelta(minutes=20),
    )
    with pytest.raises(ValueError, match="Автомобиль уже забронирован"):
        booking_repo.create(b2)
