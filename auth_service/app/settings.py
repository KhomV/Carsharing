from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_url: str
    license_service_url: str = "http://license_service:8000"
    license_status_key: SecretStr | None = None
    auth_token_ttl_seconds: int = Field(default=3600, gt=0)

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
