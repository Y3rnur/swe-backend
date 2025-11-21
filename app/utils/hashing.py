"""Password hashing utilities."""

import bcrypt

from app.core.config import settings


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with configurable cost factor.

    Uses BCRYPT_ROUNDS from settings (default: 12, recommended for 2024+).
    Higher rounds = more secure but slower (exponential cost).
    """
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)
    return password_hash.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, AttributeError, TypeError):
        return False
