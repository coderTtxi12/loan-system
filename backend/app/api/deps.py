"""API Dependencies for FastAPI."""
from typing import Annotated, AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_token, ACCESS_TOKEN_TYPE
from app.db.session import async_session_maker
from app.models.user import User, UserRole

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency.

    Yields an async database session and handles cleanup.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Type alias for database dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(security),
    ],
) -> User:
    """
    Get the current authenticated user.

    Args:
        db: Database session
        credentials: HTTP Bearer credentials

    Returns:
        Authenticated User

    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    # Verify token
    payload = verify_token(credentials.credentials, ACCESS_TOKEN_TYPE)
    if not payload:
        raise credentials_exception

    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    # Fetch user from database
    try:
        result = await db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()
    except Exception:
        raise credentials_exception

    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


# Type alias for current user dependency
CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(
    current_user: CurrentUser,
) -> User:
    """
    Get current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        Active User

    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


# Type alias for active user dependency
ActiveUser = Annotated[User, Depends(get_current_active_user)]


async def get_current_admin_user(
    current_user: CurrentUser,
) -> User:
    """
    Get current admin user.

    Args:
        current_user: Current authenticated user

    Returns:
        Admin User

    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


# Type alias for admin user dependency
AdminUser = Annotated[User, Depends(get_current_admin_user)]


async def get_current_analyst_user(
    current_user: CurrentUser,
) -> User:
    """
    Get current user with analyst or admin privileges.

    Args:
        current_user: Current authenticated user

    Returns:
        Analyst or Admin User

    Raises:
        HTTPException: If user cannot approve loans
    """
    if not current_user.can_approve_loans:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst privileges required",
        )
    return current_user


# Type alias for analyst user dependency
AnalystUser = Annotated[User, Depends(get_current_analyst_user)]


def get_optional_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(security),
    ],
) -> Optional[dict]:
    """
    Get optional user info from token (doesn't require auth).

    Args:
        credentials: Optional HTTP Bearer credentials

    Returns:
        Token payload or None
    """
    if not credentials:
        return None

    payload = verify_token(credentials.credentials, ACCESS_TOKEN_TYPE)
    return payload


# Type alias for optional user dependency
OptionalUser = Annotated[Optional[dict], Depends(get_optional_user)]
