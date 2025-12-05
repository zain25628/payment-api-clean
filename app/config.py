# Refactored by Copilot
from functools import lru_cache
from pydantic import field_validator
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
    SECRET_KEY: str

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or v == "CHANGE_ME":
            raise RuntimeError("SECRET_KEY must be set to a secure value in environment variables")
        return v

    # Defaults used for merchant onboarding and local development
    DEFAULT_MERCHANT_BASE_URL_DEV: str = "http://localhost:8000"
    DEFAULT_MERCHANT_DOCS_URL: str = "https://docs.example.com/merchant-integration"
    DEFAULT_WALLET_DAILY_LIMIT: float = 100000.0
    # Onboarding PDF output directory (relative to repo root)
    ONBOARDING_OUTPUT_DIR: str = "generated_onboarding"
    # Environment name used in generated docs
    ENVIRONMENT_NAME: str = "dev"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Module-level instance for convenience
settings = get_settings()
