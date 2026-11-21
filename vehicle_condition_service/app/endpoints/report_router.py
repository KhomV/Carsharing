from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, Security, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.clients.source_client import current_profile
from app.models.report import ConditionReport, ReportPhase
from app.services.report_service import ReportService


report_router = APIRouter(prefix="/condition-reports", tags=["Vehicle condition"])
bearer_scheme = HTTPBearer(auto_error=False)


def current_account_id(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> UUID:
    if credentials is None:
        raise HTTPException(
            status_code=401, detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_profile(credentials.credentials).id


@report_router.post("/reference/{phase}/{reference_id}", response_model=ConditionReport, status_code=201)
def create_report(
    phase: ReportPhase,
    reference_id: UUID,
    photos: Annotated[list[UploadFile], File(min_length=1, max_length=5)],
    account_id: UUID = Depends(current_account_id),
    service: ReportService = Depends(),
) -> ConditionReport:
    return service.create(account_id, phase, reference_id, photos)


@report_router.get("/reference/{phase}/{reference_id}", response_model=ConditionReport)
def get_report_by_reference(
    phase: ReportPhase, reference_id: UUID, account_id: UUID = Depends(current_account_id),
    service: ReportService = Depends(),
) -> ConditionReport:
    return service.get_by_reference(account_id, phase, reference_id)


@report_router.get("/{report_id}", response_model=ConditionReport)
def get_report(
    report_id: UUID, account_id: UUID = Depends(current_account_id),
    service: ReportService = Depends(),
) -> ConditionReport:
    return service.get(account_id, report_id)


@report_router.get("/{report_id}/photos/{photo_id}", response_class=Response)
def download_photo(
    report_id: UUID, photo_id: UUID, account_id: UUID = Depends(current_account_id),
    service: ReportService = Depends(),
) -> Response:
    photo, data = service.download(account_id, report_id, photo_id)
    return Response(data, media_type=photo.content_type, headers={
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
    })
