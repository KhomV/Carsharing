from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import Depends
from sqlalchemy.orm import Session

from app.clients.telemetry_client import TelemetryClient
from app.database import get_db
from app.models.booking import Booking, BookingStatus, CreateBookingRequest
from app.models.car import Car, CarStatus, CarWithCoordinates, CreateCarRequest
from app.repositories.db_booking_repo import BookingRepo
from app.repositories.db_car_repo import CarRepo


class BookingService:
    def __init__(
        self,
        db: Session = Depends(get_db),
        telemetry_client: TelemetryClient | None = None,
    ):
        self.car_repo = CarRepo(db)
        self.booking_repo = BookingRepo(db)
        self.telemetry_client = telemetry_client or TelemetryClient()

    def create_car(self, request: CreateCarRequest) -> Car:
        car = Car(
            id=uuid4(),
            model=request.model,
            plate_number=request.plate_number,
            status=CarStatus.AVAILABLE,
            price_per_minute=request.price_per_minute,
            created_at=datetime.now(timezone.utc),
        )
        return self.car_repo.create(car)

    def get_all_cars(self) -> list[Car]:
        return self.car_repo.get_all()

    def get_car(self, car_id: UUID) -> CarWithCoordinates:
        car = self.car_repo.get_by_id(car_id)
        telemetry = self.telemetry_client.get_car_telemetry(car_id)

        return CarWithCoordinates(
            id=car.id,
            model=car.model,
            plate_number=car.plate_number,
            status=car.status,
            price_per_minute=car.price_per_minute,
            latitude=telemetry.get("latitude") if telemetry else None,
            longitude=telemetry.get("longitude") if telemetry else None,
            fuel_level=telemetry.get("fuel_level") if telemetry else None,
            is_engine_on=telemetry.get("is_engine_on") if telemetry else None,
            is_handbrake_engaged=telemetry.get("is_handbrake_engaged")
            if telemetry
            else None,
        )

    def get_available_cars_on_map(self) -> list[CarWithCoordinates]:
        available_cars = self.car_repo.get_available()
        all_telemetry = self.telemetry_client.get_all_cars_telemetry()

        result = []
        for car in available_cars:
            telemetry = all_telemetry.get(car.id)
            result.append(
                CarWithCoordinates(
                    id=car.id,
                    model=car.model,
                    plate_number=car.plate_number,
                    status=car.status,
                    price_per_minute=car.price_per_minute,
                    latitude=telemetry.get("latitude") if telemetry else None,
                    longitude=telemetry.get("longitude") if telemetry else None,
                    fuel_level=telemetry.get("fuel_level") if telemetry else None,
                    is_engine_on=telemetry.get("is_engine_on")
                    if telemetry
                    else None,
                    is_handbrake_engaged=telemetry.get("is_handbrake_engaged")
                    if telemetry
                    else None,
                )
            )
        return result

    def create_booking(self, request: CreateBookingRequest) -> Booking:
        car = self.car_repo.get_by_id(request.car_id)

        if car.status != CarStatus.AVAILABLE:
            raise ValueError("Автомобиль недоступен для бронирования")

        user_active = self.booking_repo.get_active_by_user_id(request.user_id)
        if user_active is not None:
            raise ValueError("У пользователя уже есть активное бронирование")

        car_active = self.booking_repo.get_active_by_car_id(request.car_id)
        if car_active is not None:
            raise ValueError("Автомобиль уже забронирован")

        now = datetime.now(timezone.utc)
        booking = Booking(
            id=uuid4(),
            car_id=request.car_id,
            user_id=request.user_id,
            status=BookingStatus.ACTIVE,
            created_at=now,
            expires_at=now + timedelta(minutes=request.duration_minutes),
        )

        created_booking = self.booking_repo.create(booking)
        self.car_repo.update_status(car.id, CarStatus.BOOKED)

        return created_booking

    def cancel_booking(self, booking_id: UUID) -> Booking:
        booking = self.booking_repo.get_by_id(booking_id)

        if booking.status != BookingStatus.ACTIVE:
            raise ValueError("Отменить можно только активное бронирование")

        updated_booking = booking.model_copy(
            update={
                "status": BookingStatus.CANCELLED,
                "cancelled_at": datetime.now(timezone.utc),
            }
        )

        saved = self.booking_repo.update(updated_booking)
        self.car_repo.update_status(booking.car_id, CarStatus.AVAILABLE)

        return saved

    def complete_booking(self, booking_id: UUID) -> Booking:
        booking = self.booking_repo.get_by_id(booking_id)

        if booking.status != BookingStatus.ACTIVE:
            raise ValueError("Завершить можно только активное бронирование")

        updated_booking = booking.model_copy(
            update={"status": BookingStatus.COMPLETED}
        )

        return self.booking_repo.update(updated_booking)

    def get_booking(self, booking_id: UUID) -> Booking:
        return self.booking_repo.get_by_id(booking_id)

    def get_bookings(self, user_id: UUID | None = None) -> list[Booking]:
        return self.booking_repo.get_all(user_id=user_id)
