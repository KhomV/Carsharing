from uuid import UUID

from app.database import SessionLocal
from app.services.invoice_service import InvoiceService


with SessionLocal() as db:
    service = InvoiceService(db=db)

    invoice = service.create_invoice(
        rental_id=UUID("44444444-4444-4444-8444-444444444444"),
        user_id=UUID("11111111-1111-4111-8111-111111111111"),
        amount=1500,
    )

    print(invoice.model_dump_json(indent=2))