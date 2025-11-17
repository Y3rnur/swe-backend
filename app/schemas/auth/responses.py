"""Authentication response schemas."""

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
