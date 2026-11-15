from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.models.invoice import Invoice
from app.services.invoice_service import InvoiceService


invoice_router = APIRouter(
    prefix="/invoices",
    tags=["Счета"],
)


@invoice_router.get("", response_model=list[Invoice])
def get_invoices(
    invoice_service: InvoiceService = Depends(InvoiceService),
):
    return invoice_service.get_invoices()


@invoice_router.get("/{invoice_id}", response_model=Invoice)
def get_invoice(
    invoice_id: UUID,
    invoice_service: InvoiceService = Depends(InvoiceService),
):
    try:
        return invoice_service.get_invoice(invoice_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Счёт не найден",
        ) from error


@invoice_router.post("/{invoice_id}/pay", response_model=Invoice)
def pay_invoice(
    invoice_id: UUID,
    invoice_service: InvoiceService = Depends(InvoiceService),
):
    try:
        return invoice_service.pay_invoice(invoice_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Счёт не найден",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error