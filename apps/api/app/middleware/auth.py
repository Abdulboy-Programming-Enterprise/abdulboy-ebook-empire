"""
Authentication Middleware
=========================
JWT token validation and user authentication for protected routes.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Optional
import jwt
from app.core.config import settings
from app.core.logger import logger

# Paths that don't require authentication
PUBLIC_PATHS = [
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
    "/api/v1/health",
    "/api/v1/health/ready",
    "/api/v1/health/live",
    "/api/v1/webhooks/stripe",
    "/api/v1/webhooks/opay",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
]

# Path prefixes that are public
PUBLIC_PREFIXES = [
    "/static",
    "/uploads",
]


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate JWT tokens for protected endpoints.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public paths
        path = request.url.path
        
        if path in PUBLIC_PATHS:
            return await call_next(request)
        
        for prefix in PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            # For API routes, require authentication
            if path.startswith("/api/"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authentication token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return await call_next(request)
        
        # Extract token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
            )
        
        # Validate token
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Check token type
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )
            
            # Add user info to request state
            request.state.user_id = payload.get("sub")
            request.state.token_payload = payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        
        return await call_next(request)
