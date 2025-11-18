"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorMessages
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.db.session import get_db
from app.modules.auth.schema import (
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
)
from app.modules.user.model import User
from app.utils.hashing import hash_password, verify_password
from app.utils.helpers import get_user_by_email, get_user_by_id

AuthRouter = APIRouter(prefix="/auth", tags=["auth"])


def _create_tokens(user: User) -> TokenResponse:
    """Create access and refresh tokens for user."""
    return TokenResponse(
        access_token=create_access_token(data={"sub": user.id, "email": user.email}),
        refresh_token=create_refresh_token(data={"sub": user.id}),
        token_type="bearer",
    )


@AuthRouter.post(
    "/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user account."""
    existing_user = await get_user_by_email(request.email, db)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMessages.EMAIL_ALREADY_REGISTERED,
        )
    password_hash = hash_password(request.password)
    user = User(
        email=request.email,
        password_hash=password_hash,
        role=request.role.value,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _create_tokens(user)


@AuthRouter.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return tokens."""
    user = await get_user_by_email(request.email, db)
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessages.INCORRECT_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorMessages.USER_INACTIVE,
        )
    return _create_tokens(user)


@AuthRouter.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    payload = decode_refresh_token(request.refresh_token)
    if payload is None or (user_id := payload.get("sub")) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessages.INVALID_REFRESH_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_user_by_id(user_id, db)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessages.USER_NOT_FOUND_OR_INACTIVE,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _create_tokens(user)
