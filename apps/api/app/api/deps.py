"""
API Dependencies
================
Common dependencies for API endpoints (authentication, database, etc.).
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Union
from app.core.database import get_db
from app.core.cache import get_redis
from app.core.security import decode_token
from app.models.user import User
from app.core.exceptions import UnauthorizedException, ForbiddenException
import redis.asyncio as redis

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current authenticated user from JWT token.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException("Invalid or expired token")
    
    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type")
    
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")
    
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise UnauthorizedException("User not found")
    
    if user.deleted_at:
        raise UnauthorizedException("Account has been deactivated")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (must be authenticated).
    """
    if not current_user:
        raise UnauthorizedException("Not authenticated")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current admin user (must be admin).
    """
    if not current_user.is_admin:
        raise ForbiddenException("Admin privileges required")
    return current_user


async def get_current_special_or_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current special or admin user.
    """
    if not (current_user.is_admin or current_user.is_special):
        raise ForbiddenException("Special user or admin privileges required")
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise None.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    return user if user and not user.deleted_at else None


async def get_redis_client() -> redis.Redis:
    """
    Get Redis client for caching and rate limiting.
    """
    return await get_redis()
