from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.schemas.base_schema import Base


class RentalTable(Base):
    __tablename__ = "rentals"

    id = Column(UUID(as_uuid=True), primary_key=True)

    user_id = Column(UUID(as_uuid=True), nullable=False)
    car_id = Column(UUID(as_uuid=True), nullable=False)

    status = Column(String, nullable=False)

    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    price_per_minute = Column(Integer, nullable=False)
    total_amount = Column(Integer, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'paused', 'finished')",
            name="ck_rentals_status",
        ),
        CheckConstraint(
            "price_per_minute > 0",
            name="ck_rentals_price_positive",
        ),
        CheckConstraint(
            "total_amount IS NULL OR total_amount >= 0",
            name="ck_rentals_amount_nonnegative",
        ),
        Index(
            "uq_rentals_unfinished_car",
            "car_id",
            unique=True,
            postgresql_where=text(
                "status IN ('active', 'paused')"
            ),
        ),
    )