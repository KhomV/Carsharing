from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID

from app.schemas.base_schema import Base


class CarTable(Base):
    __tablename__ = "cars"

    id = Column(UUID(as_uuid=True), primary_key=True)
    model = Column(String, nullable=False)
    plate_number = Column(String, nullable=False, unique=True)
    status = Column(String, nullable=False)
    price_per_minute = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('available', 'booked', 'rented', 'maintenance')",
            name="ck_cars_status",
        ),
        CheckConstraint(
            "price_per_minute > 0",
            name="ck_cars_price_positive",
        ),
    )
