from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.license import LicenseDetails, LicenseState, LicenseStatus, SubmitLicense
from app.repositories.db_license_repo import LicenseRepo
from app.schemas.license import LicenseTable


def is_expired(license: LicenseTable) -> bool:
    return license.expires_on < datetime.now(timezone.utc).date()


def license_details(license: LicenseTable) -> LicenseDetails:
    return LicenseDetails(
        id=license.id, expires_on=license.expires_on, number_last_four=license.number_last_four,
        status=license.status, reason=license.reason,
    )


class LicenseService:
    def __init__(self, db: Session = Depends(get_db)):
        self.repo = LicenseRepo(db)

    def submit(self, account_id: UUID, request: SubmitLicense) -> LicenseDetails:
        license = self.repo.submit(LicenseTable(
            id=uuid4(), account_id=account_id, expires_on=request.expires_on,
            number_last_four=request.number[-4:], status=LicenseState.PENDING.value,
        ))
        details = license_details(license)
        self.repo.commit()
        return details

    def verify(self, account_id: UUID, license_id: UUID) -> LicenseDetails:
        license = self.repo.find_for_verification(license_id, account_id)
        if license is None:
            raise HTTPException(status_code=404, detail="Driver license not found")

        # The classroom verifier only checks the declared expiration date.
        expired = is_expired(license)
        license.status = LicenseState.REJECTED.value if expired else LicenseState.VERIFIED.value
        license.reason = "expired" if expired else None
        details = license_details(license)
        self.repo.commit()
        return details

    def get_status(self, account_id: UUID) -> LicenseStatus:
        license = self.repo.find_by_account(account_id)
        if license is None:
            raise HTTPException(status_code=404, detail="Driver license not found")

        status = LicenseState(license.status)
        if status == LicenseState.VERIFIED and is_expired(license):
            status = LicenseState.REJECTED
        return LicenseStatus(status=status)
