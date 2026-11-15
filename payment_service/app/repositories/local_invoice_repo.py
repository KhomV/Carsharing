#НЕ ИСПОЛЬЗУЕТСЯ

from datetime import datetime, timezone
from uuid import UUID

from app.models.invoice import Invoice, InvoiceStatus



invoices: list[Invoice] = [
    Invoice(
        id=UUID("33333333-3333-4333-8333-333333333333"),
        rental_id=UUID("44444444-4444-4444-8444-444444444444"),
        user_id=UUID("11111111-1111-4111-8111-111111111111"),
        amount=1500,
        status=InvoiceStatus.PENDING,
        created_at=datetime.now(timezone.utc),
    )
]


class InvoiceRepo:
    def get_all(self) -> list[Invoice]:
        return invoices.copy()

    def get_by_id(self, invoice_id: UUID) -> Invoice:
        for invoice in invoices:
            if invoice.id == invoice_id:
                return invoice

        raise KeyError("Счёт не найден")

    def get_by_rental_id(self, rental_id: UUID) -> Invoice | None:
        for invoice in invoices:
            if invoice.rental_id == rental_id:
                return invoice

        return None

    def create(self, invoice: Invoice) -> Invoice:
        if self.get_by_rental_id(invoice.rental_id) is not None:
            raise ValueError("Счёт для этой аренды уже существует")

        invoices.append(invoice)
        return invoice

    def update(self, invoice: Invoice) -> Invoice:
        for index, saved_invoice in enumerate(invoices):
            if saved_invoice.id == invoice.id:
                invoices[index] = invoice
                return invoice

        raise KeyError("Счёт не найден")