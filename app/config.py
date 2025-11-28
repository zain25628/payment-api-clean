# Refactored by Copilot
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Payment Gateway API"
    PROJECT_VERSION: str = "0.1.0"
    DATABASE_URL: str
    SECRET_KEY: str = "CHANGE_ME"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Module-level instance for convenience
settings = get_settings()
