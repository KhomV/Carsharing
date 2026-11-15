from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.schemas.base_schema import Base


class InvoiceTable(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True)

    rental_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)

    amount = Column(Integer, nullable=False)
    status = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "rental_id",
            name="uq_invoices_rental_id",
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_invoices_amount_positive",
        ),
        CheckConstraint(
            "status IN ('pending', 'paid')",
            name="ck_invoices_status",
        ),
    )