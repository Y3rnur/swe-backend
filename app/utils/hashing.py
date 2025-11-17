"""Password hashing utilities."""

import hashlib
import secrets


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{password_hash}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    try:
        salt, password_hash = hashed.split(":")
        test_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        return secrets.compare_digest(test_hash, password_hash)
    except (ValueError, AttributeError):
        return False
