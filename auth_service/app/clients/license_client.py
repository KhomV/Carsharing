from typing import Literal
from uuid import UUID

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError

from app.models.account import Eligibility
from app.settings import settings


class LicenseStatus(BaseModel):
    status: Literal["pending", "verified", "rejected"]


class LicenseClient:
    def get_eligibility(self, account_id: UUID) -> Eligibility:
        url = f"{settings.license_service_url.rstrip('/')}/api/users/{account_id}/license-status"
        headers = {}
        if settings.license_status_key is not None:
            headers["X-License-Status-Key"] = settings.license_status_key.get_secret_value()
        try:
            response = httpx.get(url, headers=headers, timeout=3.0)
            if response.status_code == 404:
                return Eligibility(eligible=False, license_status="missing")
            response.raise_for_status()
            status = LicenseStatus.model_validate_json(response.content).status
        except (httpx.HTTPError, ValidationError) as error:
            raise HTTPException(status_code=503, detail="License status unavailable") from error
        return Eligibility(eligible=status == "verified", license_status=status)
