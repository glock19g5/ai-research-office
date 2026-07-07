"""Application settings.

Loaded from environment / .env via pydantic-settings.
NO secrets are hardcoded here. Secret-classified values (D-014) must come
from the environment or a Secret Manager, never from the repository.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Non-secret operational config only (Phase 1: no AI/DB yet).
    app_env: str = "development"          # development | staging | production (D-014)
    log_level: str = "INFO"
    service_name: str = "aio-backend"


def get_settings() -> Settings:
    return Settings()
