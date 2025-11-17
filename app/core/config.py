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

    # Logging
    LOG_LEVEL: str = "INFO"

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI Backend Server"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A minimal, production-ready FastAPI server"

    # Environment
    ENV: str = "dev"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:2148@localhost:5432/postgres"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS - type as Union to handle both string and list from env
    CORS_ORIGINS: str | list[str] = "http://localhost:3000,http://localhost:8000"

    @model_validator(mode="before")
    @classmethod
    def parse_cors_origins(
        cls, values: dict[str, str | list[str]]
    ) -> dict[str, str | list[str]]:
        """Parse CORS origins from comma-separated string to list before validation."""
        if "CORS_ORIGINS" in values:
            cors_value = values["CORS_ORIGINS"]
            if isinstance(cors_value, str):
                # Parse comma-separated string
                values["CORS_ORIGINS"] = [
                    origin.strip() for origin in cors_value.split(",") if origin.strip()
                ]
        return values


settings = Settings()
