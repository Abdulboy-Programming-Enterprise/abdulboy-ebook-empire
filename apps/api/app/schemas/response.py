"""
Response Schemas
================
Standard API response formats.
"""

from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, List, Any

T = TypeVar('T')


class StandardResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    errors: Optional[List[Dict[str, Any]]] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    success: bool = False
    message: str
    errors: Optional[List[Dict[str, Any]]] = None
    status_code: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str
    services: Dict[str, str]


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    success: bool = True
