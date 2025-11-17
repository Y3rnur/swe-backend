"""Authentication request schemas."""

from pydantic import BaseModel, EmailStr, Field

from app.core.roles import Role


class SignupRequest(BaseModel):
    """Signup request schema."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    role: Role


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str
