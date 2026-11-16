from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


SERVICE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    postgres_url: str
    telemetry_service_url: str = "http://telemetry_service:8000"

    model_config = SettingsConfigDict(
        env_file=SERVICE_DIR / ".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
