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

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100  # Default rate limit per minute
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10  # Stricter limit for auth endpoints

    # Password policy
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False  # Optional for now

    # Observability
    SLOW_QUERY_THRESHOLD_MS: int = 1000  # Log queries slower than this (milliseconds)
    HEALTH_CHECK_TIMEOUT_SECONDS: float = 5.0  # Timeout for DB health check

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
