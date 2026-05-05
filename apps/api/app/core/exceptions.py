"""
Exception Module
================
Custom exception classes and error handlers.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception."""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.details = details


class NotFoundException(AppException):
    """Resource not found exception."""
    
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(status.HTTP_404_NOT_FOUND, message)


class UnauthorizedException(AppException):
    """Unauthorized access exception."""
    
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, message)


class ForbiddenException(AppException):
    """Forbidden access exception."""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(status.HTTP_403_FORBIDDEN, message)


class ValidationException(AppException):
    """Validation error exception."""
    
    def __init__(self, message: str = "Validation error", details: Dict[str, Any] = None):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, message, details)


class ConflictException(AppException):
    """Resource conflict exception (duplicate, etc.)."""
    
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(status.HTTP_409_CONFLICT, message)


class PaymentException(AppException):
    """Payment processing exception."""
    
    def __init__(self, message: str = "Payment processing failed"):
        super().__init__(status.HTTP_400_BAD_REQUEST, message)
