from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.rental import Rental, RentalStatus
from app.schemas.rental import RentalTable


class RentalRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, rental_id: UUID) -> Rental:
        row = self.db.get(RentalTable, rental_id)

        if row is None:
            raise KeyError("Аренда не найдена")

        return Rental.model_validate(row)

    def get_unfinished_by_car_id(self, car_id: UUID) -> Rental | None:
        statement = select(RentalTable).where(
            RentalTable.car_id == car_id,
            RentalTable.status.in_([
                RentalStatus.ACTIVE.value,
                RentalStatus.PAUSED.value,
            ]),
        )

        row = self.db.execute(statement).scalar_one_or_none()

        if row is None:
            return None

        return Rental.model_validate(row)

    def create(self, rental: Rental) -> Rental:
        row = RentalTable(
            id=rental.id,
            user_id=rental.user_id,
            car_id=rental.car_id,
            status=rental.status.value,
            started_at=rental.started_at,
            finished_at=rental.finished_at,
            price_per_minute=rental.price_per_minute,
            total_amount=rental.total_amount,
        )

        self.db.add(row)

        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()

            constraint_name = getattr(
                getattr(error.orig, "diag", None),
                "constraint_name",
                None,
            )

            if constraint_name == "uq_rentals_unfinished_car":
                raise ValueError(
                    "Автомобиль уже находится в аренде"
                ) from error

            raise

        self.db.refresh(row)

        return Rental.model_validate(row)

    def update(self, rental: Rental) -> Rental:
        row = self.db.get(RentalTable, rental.id)

        if row is None:
            raise KeyError("Аренда не найдена")

        row.status = rental.status.value
        row.finished_at = rental.finished_at
        row.total_amount = rental.total_amount

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise

        self.db.refresh(row)

        return Rental.model_validate(row)