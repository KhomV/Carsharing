from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models.invoice import Invoice, InvoiceStatus
from app.repositories.db_invoice_repo import InvoiceRepo


@pytest.fixture
def invoice():
    return Invoice(id=uuid4(), rental_id=uuid4(), user_id=uuid4(), amount=1500,
                   status=InvoiceStatus.PENDING, created_at=datetime.now(timezone.utc))


def test_save_and_reload_from_postgres(db, invoice):
    repo = InvoiceRepo(db)
    repo.create(invoice)
    db.expire_all()
    assert repo.get_by_id(invoice.id) == invoice
    assert repo.get_by_rental_id(invoice.rental_id) == invoice


def test_missing_invoice(db):
    repo = InvoiceRepo(db)
    with pytest.raises(KeyError):
        repo.get_by_id(uuid4())
    assert repo.get_by_rental_id(uuid4()) is None


def test_repeated_event_has_only_one_row(db, invoice):
    repo = InvoiceRepo(db)
    repo.create(invoice)
    duplicate = invoice.model_copy(update={"id":uuid4()})
    assert repo.create(duplicate).id == invoice.id
    assert [i.id for i in repo.get_all()] == [invoice.id]


@pytest.mark.parametrize("field,value", [("amount",3000), ("user_id",None)])
def test_conflicting_duplicate_is_rejected(db, invoice, field, value):
    repo = InvoiceRepo(db)
    repo.create(invoice)
    if field == "user_id":
        value = uuid4()
    duplicate = invoice.model_copy(update={"id":uuid4(),field:value})
    with pytest.raises(ValueError, match="другими данными"):
        repo.create(duplicate)
    assert repo.get_by_id(invoice.id) == invoice


def test_payment_saved_in_postgres(db, invoice):
    repo = InvoiceRepo(db)
    repo.create(invoice)
    paid = invoice.model_copy(update={"status":InvoiceStatus.PAID,
                                      "paid_at":datetime.now(timezone.utc)})
    repo.update(paid)
    db.expire_all()
    assert repo.get_by_id(invoice.id) == paid


def test_update_missing_invoice(db, invoice):
    with pytest.raises(KeyError):
        InvoiceRepo(db).update(invoice)
