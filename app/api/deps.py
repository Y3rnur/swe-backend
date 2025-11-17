"""API dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.roles import Role
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

_http_bearer = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_http_bearer)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token."""
    payload = decode_access_token(credentials.credentials)
    if payload is None or (user_id := payload.get("sub")) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
            if payload is None
            else "Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return user


def require_roles(*roles: Role):
    """Dependency factory to require specific roles."""

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        """Check if current user has required role."""
        try:
            user_role = Role(current_user.role)
        except ValueError:
            user_role = None
        if user_role is None or user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user

    return role_checker


async def get_current_db(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    """Get current database session."""
    return db
