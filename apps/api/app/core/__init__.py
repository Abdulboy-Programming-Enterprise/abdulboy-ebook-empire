"""
Core Package
============
Core functionality for the application including security, database, cache, logging.
"""

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    decode_token,
)

from app.core.database import get_db, engine, SessionLocal
from app.core.cache import get_redis, redis_client
from app.core.logger import logger, setup_logging
from app.core.exceptions import (
    AppException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    ValidationException,
)

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "verify_password",
    "get_password_hash",
    "decode_token",
    "get_db",
    "engine",
    "SessionLocal",
    "get_redis",
    "redis_client",
    "logger",
    "setup_logging",
    "AppException",
    "NotFoundException",
    "UnauthorizedException",
    "ForbiddenException",
    "ValidationException",
]
