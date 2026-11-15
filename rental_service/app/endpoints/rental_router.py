from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.models.rental import CreateRentalRequest, Rental
from app.services.rental_service import RentalService
import logging

from fastapi import Request
from starlette.concurrency import run_in_threadpool

from app.models.rental import RentalStatus
from app.rabbitmq import publish_rental_finished

logger = logging.getLogger(__name__)


rental_router = APIRouter(
    prefix="/rentals",
    tags=["Аренда"],
)


@rental_router.post("", response_model=Rental, status_code=201)
def start_rental(
    request: CreateRentalRequest,
    rental_service: RentalService = Depends(RentalService),
):
    try:
        return rental_service.start_rental(
            user_id=request.user_id,
            car_id=request.car_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error


@rental_router.get("/{rental_id}", response_model=Rental)
def get_rental(
    rental_id: UUID,
    rental_service: RentalService = Depends(RentalService),
):
    try:
        return rental_service.get_rental(rental_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Аренда не найдена",
        ) from error

@rental_router.post("/{rental_id}/pause", response_model=Rental)
def pause_rental(
    rental_id: UUID,
    rental_service: RentalService = Depends(RentalService),
):
    try:
        return rental_service.pause_rental(rental_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Аренда не найдена",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error


@rental_router.post("/{rental_id}/resume", response_model=Rental)
def resume_rental(
    rental_id: UUID,
    rental_service: RentalService = Depends(RentalService),
):
    try:
        return rental_service.resume_rental(rental_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Аренда не найдена",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error


@rental_router.post("/{rental_id}/finish", response_model=Rental)
async def finish_rental(
    rental_id: UUID,
    request: Request,
    rental_service: RentalService = Depends(RentalService),
):
    try:
        rental = await run_in_threadpool(
            rental_service.get_rental,
            rental_id,
        )

        if rental.status != RentalStatus.FINISHED:
            rental = await run_in_threadpool(
                rental_service.finish_rental,
                rental_id,
            )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Аренда не найдена",
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    try:
        await publish_rental_finished(
            request.app.state.rabbitmq_exchange,
            rental,
        )

    except Exception as error:
        logger.exception("Не удалось отправить событие завершения аренды")

        raise HTTPException(
            status_code=503,
            detail=(
                "Аренда завершена, но отправка события не подтверждена. "
                "Повторите запрос завершения с тем же ID."
            ),
        ) from error

    return rental