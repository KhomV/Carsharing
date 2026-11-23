import pytest
from uuid import uuid4
from datetime import datetime, timezone
from rental_service.app.models.rental import Rental, RentalStatus
from rental_service.app.repositories.db_rental_repo import RentalRepo


def test_rental_create_and_get(db):
    """Тест 1: Создание аренды в БД и ее получение по ID."""
    repo = RentalRepo(db)
    rental = Rental(
        id=uuid4(),
        user_id=uuid4(),
        car_id=uuid4(),
        status=RentalStatus.ACTIVE,
        started_at=datetime.now(timezone.utc),
        price_per_minute=1500,
    )
    repo.create(rental)

    saved = repo.get_by_id(rental.id)
    assert saved.id == rental.id
    assert saved.status == RentalStatus.ACTIVE


def test_rental_finish_update(db):
    """Тест 2: Завершение аренды и обновление статуса в БД."""
    repo = RentalRepo(db)
    rental = Rental(
        id=uuid4(),
        user_id=uuid4(),
        car_id=uuid4(),
        status=RentalStatus.ACTIVE,
        started_at=datetime.now(timezone.utc),
        price_per_minute=1500,
    )
    repo.create(rental)

    finished = rental.model_copy(update={
        "status": RentalStatus.FINISHED,
        "finished_at": datetime.now(timezone.utc),
        "total_amount": 3000,
    })
    repo.update(finished)

    updated = repo.get_by_id(rental.id)
    assert updated.status == RentalStatus.FINISHED
    assert updated.total_amount == 3000
