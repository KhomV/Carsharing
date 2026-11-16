from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.telemetry import Telemetry
from app.schemas.telemetry import TelemetryTable


class TelemetryRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, telemetry: Telemetry) -> Telemetry:
        row = TelemetryTable(
            id=telemetry.id,
            car_id=telemetry.car_id,
            latitude=telemetry.latitude,
            longitude=telemetry.longitude,
            fuel_level=telemetry.fuel_level,
            mileage=telemetry.mileage,
            is_engine_on=telemetry.is_engine_on,
            is_handbrake_engaged=telemetry.is_handbrake_engaged,
            created_at=telemetry.created_at,
        )

        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)

        return Telemetry.model_validate(row)

    def get_latest_by_car_id(self, car_id: UUID) -> Telemetry | None:
        statement = (
            select(TelemetryTable)
            .where(TelemetryTable.car_id == car_id)
            .order_by(TelemetryTable.created_at.desc())
            .limit(1)
        )

        row = self.db.execute(statement).scalar_one_or_none()

        if row is None:
            return None

        return Telemetry.model_validate(row)

    def get_latest_all_cars(self) -> list[Telemetry]:
        statement = (
            select(TelemetryTable)
            .distinct(TelemetryTable.car_id)
            .order_by(TelemetryTable.car_id, TelemetryTable.created_at.desc())
        )

        rows = self.db.execute(statement).scalars().all()

        return [Telemetry.model_validate(row) for row in rows]

    def get_history(self, car_id: UUID, limit: int = 50) -> list[Telemetry]:
        statement = (
            select(TelemetryTable)
            .where(TelemetryTable.car_id == car_id)
            .order_by(TelemetryTable.created_at.desc())
            .limit(limit)
        )

        rows = self.db.execute(statement).scalars().all()

        return [Telemetry.model_validate(row) for row in rows]
