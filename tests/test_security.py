"""Security and authentication tests."""

from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.utils.hashing import hash_password, verify_password


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        password = "test_password_123"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_produces_different_hashes(self):
        """Test that hashing the same password produces different hashes (salt)."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        # Should be different due to salt
        assert hash1 != hash2

    def test_verify_password_correct_password(self):
        """Test that verify_password returns True for correct password."""
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self):
        """Test that verify_password returns False for incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """Test that verify_password handles empty password."""
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password("", hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test that verify_password handles invalid hash gracefully."""
        password = "test_password_123"
        invalid_hash = "not_a_valid_hash"
        assert verify_password(password, invalid_hash) is False


class TestJWTTokens:
    """Tests for JWT token creation and verification."""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a string."""
        data = {"sub": 1, "email": "test@example.com"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token_valid_token(self):
        """Test that decode_access_token decodes a valid token."""
        data = {"sub": 1, "email": "test@example.com"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == 1
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded

    def test_decode_access_token_invalid_token(self):
        """Test that decode_access_token returns None for invalid token."""
        invalid_token = "invalid.token.here"
        decoded = decode_access_token(invalid_token)
        assert decoded is None

    def test_decode_access_token_expired_token(self):
        """Test that decode_access_token returns None for expired token."""
        data = {"sub": 1}
        # Create token with very short expiration
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        decoded = decode_access_token(token)
        assert decoded is None

    def test_access_token_round_trip(self):
        """Test token round-trip: create and decode."""
        original_data = {"sub": 123, "email": "user@example.com", "custom": "value"}
        token = create_access_token(original_data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == original_data["sub"]
        assert decoded["email"] == original_data["email"]
        assert decoded["custom"] == original_data["custom"]

    def test_create_refresh_token_returns_string(self):
        """Test that create_refresh_token returns a string."""
        data = {"sub": 1}
        token = create_refresh_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_refresh_token_valid_token(self):
        """Test that decode_refresh_token decodes a valid refresh token."""
        data = {"sub": 1}
        token = create_refresh_token(data)
        decoded = decode_refresh_token(token)
        assert decoded is not None
        assert decoded["sub"] == 1
        assert decoded["type"] == "refresh"
        assert "exp" in decoded

    def test_decode_refresh_token_access_token_fails(self):
        """Test that decode_refresh_token returns None for access token."""
        data = {"sub": 1}
        access_token = create_access_token(data)
        decoded = decode_refresh_token(access_token)
        assert decoded is None

    def test_decode_refresh_token_invalid_token(self):
        """Test that decode_refresh_token returns None for invalid token."""
        invalid_token = "invalid.token.here"
        decoded = decode_refresh_token(invalid_token)
        assert decoded is None

    def test_refresh_token_round_trip(self):
        """Test refresh token round-trip: create and decode."""
        original_data = {"sub": 456}
        token = create_refresh_token(original_data)
        decoded = decode_refresh_token(token)
        assert decoded is not None
        assert decoded["sub"] == original_data["sub"]
        assert decoded["type"] == "refresh"

    def test_access_token_uses_settings_expiry(self):
        """Test that access token uses expiry from settings."""
        data = {"sub": 1}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded is not None

        # Check expiration is approximately correct (within 1 minute)
        # JWT exp is Unix timestamp (int)
        exp_timestamp = decoded["exp"]
        expected_exp = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        expected_timestamp = int(expected_exp.timestamp())
        time_diff = abs(exp_timestamp - expected_timestamp)
        assert time_diff < 60  # Within 1 minute

    def test_refresh_token_uses_settings_expiry(self):
        """Test that refresh token uses expiry from settings."""
        data = {"sub": 1}
        token = create_refresh_token(data)
        decoded = decode_refresh_token(token)
        assert decoded is not None

        # Check expiration is approximately correct (within 1 minute)
        # JWT exp is Unix timestamp (int)
        exp_timestamp = decoded["exp"]
        expected_exp = datetime.now(UTC) + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )
        expected_timestamp = int(expected_exp.timestamp())
        time_diff = abs(exp_timestamp - expected_timestamp)
        assert time_diff < 60  # Within 1 minute
