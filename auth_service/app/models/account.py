from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class Credentials(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128, repr=False)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        local, separator, domain = email.partition("@")
        if not separator or not local or "." not in domain or "@" in domain or any(c.isspace() for c in email):
            raise ValueError("Invalid email address")
        return email


class RegisterRequest(Credentials):
    password: str = Field(min_length=12, max_length=128, repr=False)
    full_name: str = Field(min_length=1, max_length=200, pattern=r"\S")


class Account(BaseModel):
    id: UUID
    email: str
    full_name: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class Eligibility(BaseModel):
    eligible: bool
    license_status: str
