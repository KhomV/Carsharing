from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_url: str
    mongo_database: str = "support"
    auth_service_url: str = "http://auth_service:8000"
    rental_service_url: str = "http://rental_service:8000"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
