from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.telemetry import RecordTelemetryRequest, Telemetry
from app.repositories.db_telemetry_repo import TelemetryRepo


class TelemetryService:
    def __init__(self, db: Session = Depends(get_db)):
        self.repo = TelemetryRepo(db)

    def record_telemetry(self, request: RecordTelemetryRequest) -> Telemetry:
        telemetry = Telemetry(
            id=uuid4(),
            car_id=request.car_id,
            latitude=request.latitude,
            longitude=request.longitude,
            fuel_level=request.fuel_level,
            mileage=request.mileage,
            is_engine_on=request.is_engine_on,
            is_handbrake_engaged=request.is_handbrake_engaged,
            created_at=datetime.now(timezone.utc),
        )

        return self.repo.create(telemetry)

    def get_car_telemetry(self, car_id: UUID) -> Telemetry:
        telemetry = self.repo.get_latest_by_car_id(car_id)

        if telemetry is None:
            raise KeyError("Телеметрия для автомобиля не найдена")

        return telemetry

    def get_all_cars_telemetry(self) -> list[Telemetry]:
        return self.repo.get_latest_all_cars()

    def get_car_telemetry_history(
        self, car_id: UUID, limit: int = 50
    ) -> list[Telemetry]:
        return self.repo.get_history(car_id, limit)
