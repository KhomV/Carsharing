from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.models.invoice import Invoice, InvoiceStatus
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.db_invoice_repo import InvoiceRepo


class InvoiceService:
    def __init__(self, db: Session = Depends(get_db)):
        self.invoice_repo = InvoiceRepo(db)

    def get_invoices(self) -> list[Invoice]:
        return self.invoice_repo.get_all()

    def get_invoice(self, invoice_id: UUID) -> Invoice:
        return self.invoice_repo.get_by_id(invoice_id)

    def create_invoice(
        self,
        rental_id: UUID,
        user_id: UUID,
        amount: int,
    ) -> Invoice:
        if amount <= 0:
            raise ValueError("Сумма счёта должна быть положительной")

        existing_invoice = self.invoice_repo.get_by_rental_id(
            rental_id
        )

        if existing_invoice is not None:
            if (
                existing_invoice.user_id != user_id
                or existing_invoice.amount != amount
            ):
                raise ValueError(
                    "Получены другие данные для существующего счёта"
                )

            return existing_invoice

        invoice = Invoice(
            id=uuid4(),
            rental_id=rental_id,
            user_id=user_id,
            amount=amount,
            status=InvoiceStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )

        return self.invoice_repo.create(invoice)

    def pay_invoice(self, invoice_id: UUID) -> Invoice:
        invoice = self.invoice_repo.get_by_id(invoice_id)

        if invoice.status != InvoiceStatus.PENDING:
            raise ValueError("Счёт уже оплачен")

        updated_invoice = invoice.model_copy(
            update={
                "status": InvoiceStatus.PAID,
                "paid_at": datetime.now(timezone.utc),
            }
        )

        return self.invoice_repo.update(updated_invoice)