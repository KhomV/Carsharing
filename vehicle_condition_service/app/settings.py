from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_url: str
    auth_service_url: str = "http://auth_service:8000"
    booking_service_url: str = "http://booking_service:8000"
    rental_service_url: str = "http://rental_service:8000"
    s3_endpoint_url: str | None = None
    s3_bucket: str = "carsharing-condition-photos"
    s3_region: str = "us-east-1"
    s3_create_bucket: bool = False

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
