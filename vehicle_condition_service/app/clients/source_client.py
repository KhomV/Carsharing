from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import HTTPException
from pydantic import AwareDatetime, BaseModel, ValidationError

from app.models.report import ReportPhase
from app.settings import settings


class Profile(BaseModel):
    id: UUID


class VehicleReference(BaseModel):
    user_id: UUID
    car_id: UUID
    status: str


class BookingReference(VehicleReference):
    expires_at: AwareDatetime


def fetch(url: str, *, headers: dict[str, str] | None = None) -> httpx.Response:
    try:
        return httpx.get(url, headers=headers, timeout=3.0)
    except httpx.RequestError as error:
        raise HTTPException(status_code=503, detail="Required service unavailable") from error


def current_profile(token: str) -> Profile:
    response = fetch(
        f"{settings.auth_service_url.rstrip('/')}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    if response.status_code == 401:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return parse_response(response, Profile)


def parse_response[T: BaseModel](response: httpx.Response, schema: type[T]) -> T:
    try:
        response.raise_for_status()
        return schema.model_validate_json(response.content)
    except (httpx.HTTPError, ValidationError) as error:
        raise HTTPException(status_code=503, detail="Required service unavailable") from error


def report_car_id(phase: ReportPhase, reference_id: UUID, account_id: UUID) -> UUID:
    if phase == ReportPhase.BEFORE:
        url = f"{settings.booking_service_url.rstrip('/')}/api/bookings/{reference_id}"
        expected_status = "active"
        schema = BookingReference
    else:
        url = f"{settings.rental_service_url.rstrip('/')}/api/rentals/{reference_id}"
        expected_status = "finished"
        schema = VehicleReference

    response = fetch(url)
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Booking or rental not found")
    reference = parse_response(response, schema)
    if reference.user_id != account_id:
        raise HTTPException(status_code=404, detail="Booking or rental not found")
    if reference.status != expected_status or (
        isinstance(reference, BookingReference) and reference.expires_at <= datetime.now(timezone.utc)
    ):
        raise HTTPException(status_code=409, detail="Booking or rental is not eligible for this report")
    return reference.car_id
