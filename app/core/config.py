"""Application configuration."""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI Backend Server"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A minimal, production-ready FastAPI server"
    ENV: str = "dev"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:2148@localhost:5432/postgres"
    TEST_DATABASE_URL: str | None = None  # Optional test database URL
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    CORS_ORIGINS: str | list[str] = "http://localhost:3000,http://localhost:8000"

    @model_validator(mode="before")
    @classmethod
    def parse_cors_origins(
        cls, values: dict[str, str | list[str]]
    ) -> dict[str, str | list[str]]:
        """Parse CORS origins from comma-separated string to list."""
        if "CORS_ORIGINS" in values and isinstance(values["CORS_ORIGINS"], str):
            values["CORS_ORIGINS"] = [
                origin.strip()
                for origin in values["CORS_ORIGINS"].split(",")
                if origin.strip()
            ]
        return values


settings = Settings()
