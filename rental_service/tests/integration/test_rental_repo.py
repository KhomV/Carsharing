from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models.rental import Rental, RentalStatus
from app.repositories.db_rental_repo import RentalRepo


@pytest.fixture
def rental():
    return Rental(id=uuid4(), user_id=uuid4(), car_id=uuid4(),
                  status=RentalStatus.ACTIVE, started_at=datetime.now(timezone.utc),
                  price_per_minute=1500)


def test_save_and_reload_from_postgres(db, rental):
    repo = RentalRepo(db)
    repo.create(rental)
    db.expire_all()
    assert repo.get_by_id(rental.id) == rental


def test_missing_rental(db):
    with pytest.raises(KeyError):
        RentalRepo(db).get_by_id(uuid4())


def test_find_unfinished_rental(db, rental):
    repo = RentalRepo(db)
    repo.create(rental)
    assert repo.get_unfinished_by_car_id(rental.car_id).id == rental.id
    assert repo.get_unfinished_by_car_id(uuid4()) is None


def test_database_prevents_two_active_rentals_and_recovers(db, rental):
    repo = RentalRepo(db)
    repo.create(rental)
    second = rental.model_copy(update={"id":uuid4()})
    with pytest.raises(ValueError, match="Автомобиль"):
        repo.create(second)
    # The repository must rollback the failed save, leaving the session usable.
    assert repo.get_by_id(rental.id).id == rental.id


def test_update_and_rent_finished_car_again(db, rental):
    repo = RentalRepo(db)
    repo.create(rental)
    finished = rental.model_copy(update={
        "status":RentalStatus.FINISHED,
        "finished_at":datetime.now(timezone.utc), "total_amount":1500})
    repo.update(finished)
    db.expire_all()
    assert repo.get_by_id(rental.id) == finished
    assert repo.get_unfinished_by_car_id(rental.car_id) is None
    second = rental.model_copy(update={"id":uuid4()})
    assert repo.create(second).id == second.id


def test_update_missing_rental(db, rental):
    with pytest.raises(KeyError):
        RentalRepo(db).update(rental)
