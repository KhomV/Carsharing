from uuid import UUID

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError

from app.settings import settings


class AuthProfile(BaseModel):
    id: UUID


class AuthClient:
    def get_account_id(self, token: str) -> UUID:
        url = f"{settings.auth_service_url.rstrip('/')}/api/auth/me"
        try:
            response = httpx.get(
                url, headers={"Authorization": f"Bearer {token}"}, timeout=3.0,
            )
            if response.status_code == 401:
                raise HTTPException(
                    status_code=401, detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            response.raise_for_status()
            return AuthProfile.model_validate_json(response.content).id
        except (httpx.HTTPError, ValidationError) as error:
            raise HTTPException(status_code=503, detail="Authentication unavailable") from error
