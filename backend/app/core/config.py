from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The project root is four levels up from this file:
# config.py -> core -> app -> backend -> early_intervention
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Application settings, loaded from environment variables and the .env file."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Early Intervention Decision-Support API"
    app_env: Literal["development", "test", "production"] = "development"

    database_url: str = Field(..., description="SQLAlchemy URL for the main database")
    test_database_url: str | None = None

    # Signing key for login tokens. The minimum length keeps it hard to guess.
    jwt_secret_key: str = Field(..., min_length=32, description="Signing key for login tokens")
    jwt_algorithm: Literal["HS256"] = "HS256"
    # Tokens expire after this many minutes, so a stolen token has a limited life.
    access_token_minutes: int = Field(default=60, ge=5, le=1440)

    @field_validator("database_url", "test_database_url")
    @classmethod
    def must_use_postgresql(cls, value: str | None) -> str | None:
        """Reject any database URL that doesn't use the PostgreSQL psycopg driver."""
        if value is None:
            return value
        if not value.startswith("postgresql+psycopg://"):
            raise ValueError(
                "Database URL must start with 'postgresql+psycopg://'. "
                "This project uses PostgreSQL only."
            )
        return value

    @field_validator("jwt_secret_key")
    @classmethod
    def reject_placeholder_secret(cls, value: str) -> str:
        """Stop the example placeholder from being used as a real signing key."""
        if "replace" in value.lower():
            raise ValueError("JWT_SECRET_KEY still has the placeholder value. Generate a real key.")
        return value


@lru_cache
def get_settings() -> Settings:
    """Create the Settings object once and reuse it everywhere."""
    return Settings()