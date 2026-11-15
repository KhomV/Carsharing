from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.models.rental import Rental, RentalStatus
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.db_rental_repo import RentalRepo
from app.services.pricing import calculate_rental_cost


class RentalService:
    def __init__(self, db: Session = Depends(get_db)):
        self.rental_repo = RentalRepo(db)

    def get_rental(self, rental_id: UUID) -> Rental:
        return self.rental_repo.get_by_id(rental_id)

    def start_rental(self, user_id: UUID, car_id: UUID) -> Rental:
        unfinished_rental = self.rental_repo.get_unfinished_by_car_id(
            car_id
        )

        if unfinished_rental is not None:
            raise ValueError("Автомобиль уже находится в аренде")

        rental = Rental(
            id=uuid4(),
            user_id=user_id,
            car_id=car_id,
            status=RentalStatus.ACTIVE,
            started_at=datetime.now(timezone.utc),
            price_per_minute=1500,
        )

        return self.rental_repo.create(rental)

    def pause_rental(self, rental_id: UUID) -> Rental:
        rental = self.rental_repo.get_by_id(rental_id)

        if rental.status != RentalStatus.ACTIVE:
            raise ValueError(
                "Поставить на паузу можно только активную аренду"
            )

        updated_rental = rental.model_copy(
            update={"status": RentalStatus.PAUSED}
        )

        return self.rental_repo.update(updated_rental)

    def resume_rental(self, rental_id: UUID) -> Rental:
        rental = self.rental_repo.get_by_id(rental_id)

        if rental.status != RentalStatus.PAUSED:
            raise ValueError(
                "Возобновить можно только аренду на паузе"
            )

        updated_rental = rental.model_copy(
            update={"status": RentalStatus.ACTIVE}
        )

        return self.rental_repo.update(updated_rental)

    def finish_rental(self, rental_id: UUID) -> Rental:
        rental = self.rental_repo.get_by_id(rental_id)

        if rental.status == RentalStatus.FINISHED:
            raise ValueError("Аренда уже завершена")

        finished_at = datetime.now(timezone.utc)

        total_amount = calculate_rental_cost(
            started_at=rental.started_at,
            finished_at=finished_at,
            price_per_minute=rental.price_per_minute,
        )

        updated_rental = rental.model_copy(
            update={
                "status": RentalStatus.FINISHED,
                "finished_at": finished_at,
                "total_amount": total_amount,
            }
        )

        return self.rental_repo.update(updated_rental)