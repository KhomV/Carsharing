from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from uuid import uuid4

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.account import AccessToken, Account, Credentials, RegisterRequest
from app.repositories.db_account_repo import AccountRepo
from app.schemas.account import AccountTable
from app.services.security import hash_password, token_digest, verify_password
from app.settings import settings


UNKNOWN_ACCOUNT_HASH = "0" * 32 + ":" + "0" * 64


class AuthService:
    def __init__(self, db: Session = Depends(get_db)):
        self.repo = AccountRepo(db)

    def register(self, request: RegisterRequest) -> Account:
        account = Account(id=uuid4(), email=request.email, full_name=request.full_name.strip())
        row = AccountTable(**account.model_dump(), password_hash=hash_password(request.password))
        if not self.repo.create(row):
            raise HTTPException(status_code=409, detail="Email already registered")
        return account

    def login(self, request: Credentials) -> AccessToken:
        account = self.repo.find_by_email(request.email)
        stored_hash = account.password_hash if account else UNKNOWN_ACCOUNT_HASH
        if not verify_password(request.password, stored_hash) or account is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = token_urlsafe(32)
        ttl = settings.auth_token_ttl_seconds
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        self.repo.create_session(account.id, token_digest(token), expires_at)
        return AccessToken(access_token=token, expires_in=ttl)

    def authenticate(self, token: str) -> Account:
        account = self.repo.find_by_session(token_digest(token), datetime.now(timezone.utc))
        if account is None:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return Account(id=account.id, email=account.email, full_name=account.full_name)
