from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingStatus
from app.schemas.booking import BookingTable


class BookingRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, booking_id: UUID) -> Booking:
        row = self.db.get(BookingTable, booking_id)
        if row is None:
            raise KeyError("Бронирование не найдено")
        return Booking.model_validate(row)

    def get_all(self, user_id: UUID | None = None) -> list[Booking]:
        statement = select(BookingTable).order_by(BookingTable.created_at.desc())
        if user_id is not None:
            statement = statement.where(BookingTable.user_id == user_id)
        rows = self.db.execute(statement).scalars().all()
        return [Booking.model_validate(row) for row in rows]

    def get_active_by_car_id(self, car_id: UUID) -> Booking | None:
        statement = select(BookingTable).where(
            BookingTable.car_id == car_id,
            BookingTable.status == BookingStatus.ACTIVE.value,
        )
        row = self.db.execute(statement).scalar_one_or_none()
        if row is None:
            return None
        return Booking.model_validate(row)

    def get_active_by_user_id(self, user_id: UUID) -> Booking | None:
        statement = select(BookingTable).where(
            BookingTable.user_id == user_id,
            BookingTable.status == BookingStatus.ACTIVE.value,
        )
        row = self.db.execute(statement).scalar_one_or_none()
        if row is None:
            return None
        return Booking.model_validate(row)

    def create(self, booking: Booking) -> Booking:
        row = BookingTable(
            id=booking.id,
            car_id=booking.car_id,
            user_id=booking.user_id,
            status=booking.status.value,
            created_at=booking.created_at,
            expires_at=booking.expires_at,
            cancelled_at=booking.cancelled_at,
        )

        self.db.add(row)
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise ValueError(
                "Автомобиль уже забронирован другим пользователем"
            ) from error

        self.db.refresh(row)
        return Booking.model_validate(row)

    def update(self, booking: Booking) -> Booking:
        row = self.db.get(BookingTable, booking.id)
        if row is None:
            raise KeyError("Бронирование не найдено")

        row.status = booking.status.value
        row.cancelled_at = booking.cancelled_at

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise

        self.db.refresh(row)
        return Booking.model_validate(row)
