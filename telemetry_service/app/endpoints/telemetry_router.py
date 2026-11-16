from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.telemetry import RecordTelemetryRequest, Telemetry
from app.services.telemetry_service import TelemetryService


telemetry_router = APIRouter(
    prefix="/telemetry",
    tags=["Телеметрия"],
)


@telemetry_router.post("", response_model=Telemetry, status_code=201)
def record_telemetry(
    request: RecordTelemetryRequest,
    service: TelemetryService = Depends(TelemetryService),
):
    try:
        return service.record_telemetry(request)
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error


@telemetry_router.get("/cars/{car_id}", response_model=Telemetry)
def get_car_telemetry(
    car_id: UUID,
    service: TelemetryService = Depends(TelemetryService),
):
    try:
        return service.get_car_telemetry(car_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Телеметрия для автомобиля не найдена",
        ) from error


@telemetry_router.get("/cars", response_model=list[Telemetry])
def get_all_cars_telemetry(
    service: TelemetryService = Depends(TelemetryService),
):
    return service.get_all_cars_telemetry()


@telemetry_router.get(
    "/cars/{car_id}/history", response_model=list[Telemetry]
)
def get_car_telemetry_history(
    car_id: UUID,
    limit: int = Query(default=50, ge=1, le=500),
    service: TelemetryService = Depends(TelemetryService),
):
    return service.get_car_telemetry_history(car_id=car_id, limit=limit)
