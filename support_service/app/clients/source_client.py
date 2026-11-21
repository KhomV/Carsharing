from uuid import UUID

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError

from app.settings import settings


class Profile(BaseModel):
    id: UUID


class RentalReference(BaseModel):
    user_id: UUID
    car_id: UUID


def fetch(url: str, *, headers: dict[str, str] | None = None) -> httpx.Response:
    try:
        return httpx.get(url, headers=headers, timeout=3.0)
    except httpx.RequestError as error:
        raise HTTPException(status_code=503, detail="Required service unavailable") from error


def parse_response[T: BaseModel](response: httpx.Response, schema: type[T]) -> T:
    try:
        response.raise_for_status()
        return schema.model_validate_json(response.content)
    except (httpx.HTTPError, ValidationError) as error:
        raise HTTPException(status_code=503, detail="Required service unavailable") from error


def current_account_id(token: str) -> UUID:
    response = fetch(
        f"{settings.auth_service_url.rstrip('/')}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    if response.status_code == 401:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return parse_response(response, Profile).id


def rental_car_id(account_id: UUID, rental_id: UUID) -> UUID:
    response = fetch(f"{settings.rental_service_url.rstrip('/')}/api/rentals/{rental_id}")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Rental not found")
    rental = parse_response(response, RentalReference)
    if rental.user_id != account_id:
        raise HTTPException(status_code=404, detail="Rental not found")
    return rental.car_id
