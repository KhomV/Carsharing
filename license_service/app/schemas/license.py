from datetime import date
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.schemas.base_schema import Base


class LicenseTable(Base):
    __tablename__ = "driver_licenses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'verified', 'rejected')",
            name="ck_driver_licenses_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    account_id: Mapped[UUID] = mapped_column(Uuid, unique=True)
    expires_on: Mapped[date] = mapped_column(Date)
    number_last_four: Mapped[str] = mapped_column(String(4))
    status: Mapped[str] = mapped_column(String(8))
    reason: Mapped[str | None] = mapped_column(String(40))
