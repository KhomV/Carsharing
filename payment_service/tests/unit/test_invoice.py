from datetime import datetime, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.invoice import Invoice, InvoiceStatus
from app.repositories.db_invoice_repo import InvoiceRepo
from app.services.invoice_service import InvoiceService


@pytest.fixture
def invoice_data():
    return dict(id=uuid4(), rental_id=uuid4(), user_id=uuid4(), amount=1500,
                status=InvoiceStatus.PENDING, created_at=datetime.now(timezone.utc))


@pytest.fixture
def service():
    repo = Mock(spec=InvoiceRepo)
    repo.get_by_rental_id.return_value = None
    repo.create.side_effect = lambda invoice: invoice
    repo.update.side_effect = lambda invoice: invoice
    with patch("app.services.invoice_service.InvoiceRepo", return_value=repo):
        yield InvoiceService(db=None), repo


@pytest.mark.parametrize("field", ["id","rental_id","user_id","amount","status","created_at"])
def test_model_requires_fields(invoice_data, field):
    invoice_data.pop(field)
    with pytest.raises(ValidationError):
        Invoice(**invoice_data)


@pytest.mark.parametrize("field,value", [("amount",0), ("amount",-1),
                                       ("status","unknown"), ("rental_id","bad-uuid")])
def test_model_rejects_invalid_values(invoice_data, field, value):
    invoice_data[field] = value
    with pytest.raises(ValidationError):
        Invoice(**invoice_data)


def test_model_defaults(invoice_data):
    assert Invoice(**invoice_data).paid_at is None


def test_create_invoice(service):
    app, repo = service
    rental_id, user_id = uuid4(), uuid4()
    invoice = app.create_invoice(rental_id, user_id, 1500)
    assert invoice.rental_id == rental_id and invoice.user_id == user_id
    assert invoice.amount == 1500 and invoice.status == InvoiceStatus.PENDING
    repo.create.assert_called_once_with(invoice)


def test_repeated_event_does_not_create_invoice(service, invoice_data):
    app, repo = service
    invoice = Invoice(**invoice_data)
    repo.get_by_rental_id.return_value = invoice
    assert app.create_invoice(invoice.rental_id, invoice.user_id, invoice.amount) == invoice
    repo.create.assert_not_called()


@pytest.mark.parametrize("change", [{"amount":3000}, {"user_id":None}])
def test_conflicting_event_rejected(service, invoice_data, change):
    app, repo = service
    invoice = Invoice(**invoice_data)
    repo.get_by_rental_id.return_value = invoice
    data = dict(rental_id=invoice.rental_id, user_id=invoice.user_id, amount=invoice.amount)
    data.update(change)
    with pytest.raises(ValueError):
        app.create_invoice(**data)
    repo.create.assert_not_called()


@pytest.mark.parametrize("amount", [0,-1])
def test_nonpositive_amount(service, amount):
    app, repo = service
    with pytest.raises(ValueError):
        app.create_invoice(uuid4(), uuid4(), amount)
    repo.create.assert_not_called()


def test_pay_invoice(service, invoice_data):
    app, repo = service
    original = Invoice(**invoice_data)
    repo.get_by_id.return_value = original
    paid = app.pay_invoice(original.id)
    assert paid.status == InvoiceStatus.PAID and paid.paid_at is not None
    assert original.status == InvoiceStatus.PENDING
    repo.update.assert_called_once_with(paid)


def test_cannot_pay_twice(service, invoice_data):
    app, repo = service
    repo.get_by_id.return_value = Invoice(**(invoice_data | {"status":InvoiceStatus.PAID}))
    with pytest.raises(ValueError):
        app.pay_invoice(invoice_data["id"])
    repo.update.assert_not_called()


@pytest.mark.parametrize("method", ["get_invoice","pay_invoice"])
def test_missing_invoice(service, method):
    app, repo = service
    repo.get_by_id.side_effect = KeyError("missing")
    with pytest.raises(KeyError):
        getattr(app, method)(uuid4())
    repo.update.assert_not_called()
