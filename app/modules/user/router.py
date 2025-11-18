"""User routes."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.modules.user.model import User
from app.modules.user.schema import UserResponse

UserRouter = APIRouter(prefix="/users", tags=["users"])


@UserRouter.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Get current authenticated user."""
    return current_user
