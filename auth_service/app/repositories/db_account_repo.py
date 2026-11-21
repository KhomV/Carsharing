from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.schemas.account import AccountTable, SessionTable


class AccountRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, account: AccountTable) -> bool:
        statement = (
            insert(AccountTable)
            .values(
                id=account.id,
                email=account.email,
                full_name=account.full_name,
                password_hash=account.password_hash,
            )
            .on_conflict_do_nothing(index_elements=[AccountTable.email])
            .returning(AccountTable.id)
        )
        created = self.db.scalar(statement) is not None
        self.db.commit()
        return created

    def find_by_email(self, email: str) -> AccountTable | None:
        return self.db.scalar(select(AccountTable).where(AccountTable.email == email))

    def create_session(self, account_id: UUID, digest: str, expires_at: datetime) -> None:
        self.db.add(SessionTable(account_id=account_id, token_digest=digest, expires_at=expires_at))
        self.db.commit()

    def find_by_session(self, digest: str, now: datetime) -> AccountTable | None:
        return self.db.scalar(
            select(AccountTable)
            .join(SessionTable)
            .where(SessionTable.token_digest == digest, SessionTable.expires_at > now)
        )
