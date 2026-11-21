from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.schemas.base_schema import Base


class ReportTable(Base):
    __tablename__ = "condition_reports"
    __table_args__ = (
        UniqueConstraint("phase", "reference_id", name="uq_condition_reports_reference"),
        CheckConstraint("phase IN ('before', 'after')", name="ck_condition_reports_phase"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    account_id: Mapped[UUID] = mapped_column(Uuid)
    car_id: Mapped[UUID] = mapped_column(Uuid)
    reference_id: Mapped[UUID] = mapped_column(Uuid)
    phase: Mapped[str] = mapped_column(String(6))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    photos: Mapped[list[dict]] = mapped_column(JSONB)
