from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.rental import Rental, RentalStatus
from app.repositories.db_rental_repo import RentalRepo
from app.services.pricing import calculate_rental_cost
from app.services.rental_service import RentalService

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def rental_data():
    return dict(id=uuid4(), user_id=uuid4(), car_id=uuid4(),
                status=RentalStatus.ACTIVE, started_at=NOW - timedelta(seconds=61),
                price_per_minute=1500)


@pytest.fixture
def service():
    repo = Mock(spec=RentalRepo)
    repo.get_unfinished_by_car_id.return_value = None
    repo.create.side_effect = lambda rental: rental
    repo.update.side_effect = lambda rental: rental
    with patch("app.services.rental_service.RentalRepo", return_value=repo):
        yield RentalService(db=None), repo


@pytest.mark.parametrize("seconds,amount", [(0,1500), (1,1500), (59,1500),
                                           (60,1500), (61,3000), (120,3000)])
def test_price_rounds_started_minutes(seconds, amount):
    assert calculate_rental_cost(NOW, NOW + timedelta(seconds=seconds), 1500) == amount


def test_price_rejects_negative_duration():
    with pytest.raises(ValueError):
        calculate_rental_cost(NOW, NOW - timedelta(seconds=1), 1500)


@pytest.mark.parametrize("field", ["id", "user_id", "car_id", "status", "started_at", "price_per_minute"])
def test_model_requires_fields(rental_data, field):
    rental_data.pop(field)
    with pytest.raises(ValidationError):
        Rental(**rental_data)


@pytest.mark.parametrize("field,value", [("price_per_minute",0), ("price_per_minute",-1),
                                       ("status","unknown"), ("car_id","not-a-uuid"),
                                       ("total_amount",-1)])
def test_model_rejects_invalid_values(rental_data, field, value):
    rental_data[field] = value
    with pytest.raises(ValidationError):
        Rental(**rental_data)


def test_model_defaults(rental_data):
    rental = Rental(**rental_data)
    assert rental.finished_at is None and rental.total_amount is None


def test_start_rental(service):
    app, repo = service
    user_id, car_id = uuid4(), uuid4()
    rental = app.start_rental(user_id, car_id)
    assert rental.user_id == user_id and rental.car_id == car_id
    assert rental.status == RentalStatus.ACTIVE and rental.price_per_minute == 1500
    repo.create.assert_called_once_with(rental)


def test_start_busy_car_does_not_save(service, rental_data):
    app, repo = service
    repo.get_unfinished_by_car_id.return_value = Rental(**rental_data)
    with pytest.raises(ValueError):
        app.start_rental(uuid4(), rental_data["car_id"])
    repo.create.assert_not_called()


@pytest.mark.parametrize("method,initial,expected", [
    ("pause_rental",RentalStatus.ACTIVE,RentalStatus.PAUSED),
    ("resume_rental",RentalStatus.PAUSED,RentalStatus.ACTIVE)])
def test_valid_status_transition(service, rental_data, method, initial, expected):
    app, repo = service
    original = Rental(**(rental_data | {"status": initial}))
    repo.get_by_id.return_value = original
    result = getattr(app, method)(original.id)
    assert result.status == expected and original.status == initial
    repo.update.assert_called_once_with(result)


@pytest.mark.parametrize("method,status", [
    ("pause_rental",RentalStatus.PAUSED), ("pause_rental",RentalStatus.FINISHED),
    ("resume_rental",RentalStatus.ACTIVE), ("resume_rental",RentalStatus.FINISHED),
    ("finish_rental",RentalStatus.FINISHED)])
def test_invalid_transition_does_not_save(service, rental_data, method, status):
    app, repo = service
    repo.get_by_id.return_value = Rental(**(rental_data | {"status": status}))
    with pytest.raises(ValueError):
        getattr(app, method)(rental_data["id"])
    repo.update.assert_not_called()


@pytest.mark.parametrize("status", [RentalStatus.ACTIVE, RentalStatus.PAUSED])
def test_finish_calculates_price(service, rental_data, status):
    app, repo = service
    repo.get_by_id.return_value = Rental(**(rental_data | {"status":status}))
    with patch("app.services.rental_service.datetime") as clock:
        clock.now.return_value = NOW
        result = app.finish_rental(rental_data["id"])
    assert result.status == RentalStatus.FINISHED
    assert result.finished_at == NOW and result.total_amount == 3000


@pytest.mark.parametrize("method", ["get_rental", "pause_rental", "resume_rental", "finish_rental"])
def test_missing_rental(service, method):
    app, repo = service
    repo.get_by_id.side_effect = KeyError("missing")
    with pytest.raises(KeyError):
        getattr(app, method)(uuid4())
    repo.update.assert_not_called()
