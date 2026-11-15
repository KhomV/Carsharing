from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceTable


class InvoiceRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Invoice]:
        statement = select(InvoiceTable).order_by(
            InvoiceTable.created_at,
            InvoiceTable.id,
        )

        rows = self.db.execute(statement).scalars().all()

        return [
            Invoice.model_validate(row)
            for row in rows
        ]

    def get_by_id(self, invoice_id: UUID) -> Invoice:
        row = self.db.get(InvoiceTable, invoice_id)

        if row is None:
            raise KeyError("Счёт не найден")

        return Invoice.model_validate(row)

    def get_by_rental_id(self, rental_id: UUID) -> Invoice | None:
        statement = select(InvoiceTable).where(
            InvoiceTable.rental_id == rental_id
        )

        row = self.db.execute(statement).scalar_one_or_none()

        if row is None:
            return None

        return Invoice.model_validate(row)

    def create(self, invoice: Invoice) -> Invoice:
        row = InvoiceTable(
            id=invoice.id,
            rental_id=invoice.rental_id,
            user_id=invoice.user_id,
            amount=invoice.amount,
            status=invoice.status.value,
            created_at=invoice.created_at,
            paid_at=invoice.paid_at,
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

            if constraint_name == "uq_invoices_rental_id":
                existing_invoice = self.get_by_rental_id(
                    invoice.rental_id
                )

                if existing_invoice is not None:
                    if (
                        existing_invoice.user_id == invoice.user_id
                        and existing_invoice.amount == invoice.amount
                    ):
                        return existing_invoice

                raise ValueError(
                    "Счёт для этой аренды уже существует "
                    "с другими данными"
                ) from error

            raise

        self.db.refresh(row)

        return Invoice.model_validate(row)

    def update(self, invoice: Invoice) -> Invoice:
        row = self.db.get(InvoiceTable, invoice.id)

        if row is None:
            raise KeyError("Счёт не найден")

        row.status = invoice.status.value
        row.paid_at = invoice.paid_at

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise

        self.db.refresh(row)

        return Invoice.model_validate(row)