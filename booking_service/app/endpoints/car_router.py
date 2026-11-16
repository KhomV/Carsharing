from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.models.car import Car, CarWithCoordinates, CreateCarRequest
from app.services.booking_service import BookingService


car_router = APIRouter(
    prefix="/cars",
    tags=["Автомобили"],
)


@car_router.post("", response_model=Car, status_code=201)
def create_car(
    request: CreateCarRequest,
    service: BookingService = Depends(BookingService),
):
    try:
        return service.create_car(request)
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error


@car_router.get("", response_model=list[Car])
def get_cars(
    service: BookingService = Depends(BookingService),
):
    return service.get_all_cars()


@car_router.get("/available", response_model=list[CarWithCoordinates])
def get_available_cars_on_map(
    service: BookingService = Depends(BookingService),
):
    """Поиск доступных автомобилей с получением координат от Телеметрии для отображения на карте."""
    return service.get_available_cars_on_map()


@car_router.get("/{car_id}", response_model=CarWithCoordinates)
def get_car(
    car_id: UUID,
    service: BookingService = Depends(BookingService),
):
    try:
        return service.get_car(car_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Автомобиль не найден",
        ) from error
