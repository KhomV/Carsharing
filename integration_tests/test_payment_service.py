import pytest
from uuid import uuid4
from datetime import datetime, timezone
from payment_service.app.models.invoice import Invoice, InvoiceStatus
from payment_service.app.repositories.db_invoice_repo import InvoiceRepo


def test_invoice_create_and_get(db):
    """Тест 1: Создание счета на оплату и поиск по ID."""
    repo = InvoiceRepo(db)
    invoice = Invoice(
        id=uuid4(),
        rental_id=uuid4(),
        user_id=uuid4(),
        amount=2500,
        status=InvoiceStatus.PENDING,
        created_at=datetime.now(timezone.utc),
    )
    repo.create(invoice)

    saved = repo.get_by_id(invoice.id)
    assert saved.id == invoice.id
    assert saved.amount == 2500
    assert saved.status == InvoiceStatus.PENDING


def test_invoice_pay_update(db):
    """Тест 2: Оплата счета (перевод в PAID) и обновление в БД."""
    repo = InvoiceRepo(db)
    invoice = Invoice(
        id=uuid4(),
        rental_id=uuid4(),
        user_id=uuid4(),
        amount=2500,
        status=InvoiceStatus.PENDING,
        created_at=datetime.now(timezone.utc),
    )
    repo.create(invoice)

    paid = invoice.model_copy(update={
        "status": InvoiceStatus.PAID,
        "paid_at": datetime.now(timezone.utc),
    })
    repo.update(paid)

    updated = repo.get_by_id(invoice.id)
    assert updated.status == InvoiceStatus.PAID
    assert updated.paid_at is not None
