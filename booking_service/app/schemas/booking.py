from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.schemas.base_schema import Base


class BookingTable(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True)
    car_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'cancelled', 'completed')",
            name="ck_bookings_status",
        ),
        Index(
            "uq_active_booking_car",
            "car_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )
