from hmac import compare_digest
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.clients.auth_client import AuthClient
from app.models.license import LicenseDetails, LicenseStatus, SubmitLicense
from app.services.license_service import LicenseService
from app.settings import settings


license_router = APIRouter(tags=["Driver licenses"])
bearer_scheme = HTTPBearer(auto_error=False)
status_key_scheme = APIKeyHeader(name="X-License-Status-Key", auto_error=False)


def current_account_id(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> UUID:
    if credentials is None:
        raise HTTPException(
            status_code=401, detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AuthClient().get_account_id(credentials.credentials)


def require_status_key(key: str | None = Security(status_key_scheme)) -> None:
    expected = settings.license_status_key.get_secret_value()
    if not key or not compare_digest(key.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid service credential")


@license_router.post("/licenses", response_model=LicenseDetails, status_code=201)
def submit_license(
    request: SubmitLicense,
    account_id: UUID = Depends(current_account_id),
    service: LicenseService = Depends(),
) -> LicenseDetails:
    return service.submit(account_id, request)


@license_router.post("/licenses/{license_id}/verify", response_model=LicenseDetails)
def verify_license(
    license_id: UUID,
    account_id: UUID = Depends(current_account_id),
    service: LicenseService = Depends(),
) -> LicenseDetails:
    return service.verify(account_id, license_id)


@license_router.get(
    "/users/{account_id}/license-status",
    response_model=LicenseStatus,
    dependencies=[Depends(require_status_key)],
)
def get_license_status(account_id: UUID, service: LicenseService = Depends()) -> LicenseStatus:
    return service.get_status(account_id)
