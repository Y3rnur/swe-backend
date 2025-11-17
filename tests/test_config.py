"""Configuration tests."""

import os
from unittest.mock import patch

from app.core.config import Settings


def test_env_file_loading():
    """Test that .env file values override defaults."""
    # Test with explicit env vars
    with patch.dict(
        os.environ,
        {
            "ENV": "test",
            "LOG_LEVEL": "DEBUG",
            "SECRET_KEY": "test-secret-key",
        },
        clear=False,
    ):
        settings = Settings()
        assert settings.ENV == "test"
        assert settings.LOG_LEVEL == "DEBUG"
        assert settings.SECRET_KEY == "test-secret-key"


def test_cors_origins_parsing():
    """Test that CORS origins are parsed correctly from string."""
    with patch.dict(
        os.environ,
        {
            "CORS_ORIGINS": "http://localhost:3000,http://localhost:8000,https://example.com"
        },
        clear=False,
    ):
        settings = Settings()
        assert isinstance(settings.CORS_ORIGINS, list)
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:8000" in settings.CORS_ORIGINS
        assert "https://example.com" in settings.CORS_ORIGINS


def test_all_required_settings_present():
    """Test that all required settings are present."""
    settings = Settings()

    assert hasattr(settings, "ENV")
    assert hasattr(settings, "SECRET_KEY")
    assert hasattr(settings, "ALGORITHM")
    assert hasattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES")
    assert hasattr(settings, "REFRESH_TOKEN_EXPIRE_MINUTES")
    assert hasattr(settings, "CORS_ORIGINS")
    assert hasattr(settings, "DATABASE_URL")
    assert hasattr(settings, "LOG_LEVEL")

    # Verify they have values
    assert settings.ENV is not None
    assert settings.SECRET_KEY is not None
    assert settings.DATABASE_URL is not None
