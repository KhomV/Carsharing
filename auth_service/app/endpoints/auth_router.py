from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.clients.license_client import LicenseClient
from app.models.account import AccessToken, Account, Credentials, Eligibility, RegisterRequest
from app.services.auth_service import AuthService


auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer_scheme = HTTPBearer(auto_error=False)


def current_account(
    authentication: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    service: AuthService = Depends(),
) -> Account:
    if authentication is None:
        raise HTTPException(
            status_code=401, detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return service.authenticate(authentication.credentials)


@auth_router.post("/register", response_model=Account, status_code=201)
def register(request: RegisterRequest, service: AuthService = Depends()) -> Account:
    return service.register(request)


@auth_router.post("/login", response_model=AccessToken)
def login(request: Credentials, response: Response, service: AuthService = Depends()) -> AccessToken:
    token = service.login(request)
    response.headers["Cache-Control"] = "no-store"
    return token


@auth_router.get("/me", response_model=Account)
def get_profile(account: Account = Depends(current_account)) -> Account:
    return account


@auth_router.get("/me/eligibility", response_model=Eligibility)
def get_eligibility(account: Account = Depends(current_account)) -> Eligibility:
    return LicenseClient().get_eligibility(account.id)
