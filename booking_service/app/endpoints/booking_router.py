from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.booking import Booking, CreateBookingRequest
from app.services.booking_service import BookingService


booking_router = APIRouter(
    prefix="/bookings",
    tags=["Бронирование"],
)


@booking_router.post("", response_model=Booking, status_code=201)
def create_booking(
    request: CreateBookingRequest,
    service: BookingService = Depends(BookingService),
):
    try:
        return service.create_booking(request)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error


@booking_router.get("", response_model=list[Booking])
def get_bookings(
    user_id: UUID | None = Query(default=None),
    service: BookingService = Depends(BookingService),
):
    return service.get_bookings(user_id=user_id)


@booking_router.get("/{booking_id}", response_model=Booking)
def get_booking(
    booking_id: UUID,
    service: BookingService = Depends(BookingService),
):
    try:
        return service.get_booking(booking_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Бронирование не найдено",
        ) from error


@booking_router.post("/{booking_id}/cancel", response_model=Booking)
def cancel_booking(
    booking_id: UUID,
    service: BookingService = Depends(BookingService),
):
    try:
        return service.cancel_booking(booking_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Бронирование не найдено",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error


@booking_router.post("/{booking_id}/complete", response_model=Booking)
def complete_booking(
    booking_id: UUID,
    service: BookingService = Depends(BookingService),
):
    try:
        return service.complete_booking(booking_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Бронирование не найдено",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error
