from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.schemas.license import LicenseTable


class LicenseRepo:
    def __init__(self, db: Session):
        self.db = db

    def submit(self, license: LicenseTable) -> LicenseTable:
        statement = insert(LicenseTable).values(
            id=license.id,
            account_id=license.account_id,
            expires_on=license.expires_on,
            number_last_four=license.number_last_four,
            status=license.status,
            reason=None,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[LicenseTable.account_id],
            set_={
                "id": statement.excluded.id,
                "expires_on": statement.excluded.expires_on,
                "number_last_four": statement.excluded.number_last_four,
                "status": statement.excluded.status,
                "reason": None,
            },
        ).returning(LicenseTable)
        return self.db.scalars(statement).one()

    def find_for_verification(self, license_id: UUID, account_id: UUID) -> LicenseTable | None:
        return self.db.scalar(
            select(LicenseTable)
            .where(LicenseTable.id == license_id, LicenseTable.account_id == account_id)
            .with_for_update()
        )

    def find_by_account(self, account_id: UUID) -> LicenseTable | None:
        return self.db.scalar(select(LicenseTable).where(LicenseTable.account_id == account_id))

    def commit(self) -> None:
        self.db.commit()
