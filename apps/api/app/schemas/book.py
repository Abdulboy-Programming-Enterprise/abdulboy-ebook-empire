"""
Book Schemas
=============
Pydantic schemas for book-related operations.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class BookBase(BaseModel):
    """Base book schema."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    author_name: str = Field(..., min_length=1, max_length=255)
    total_pages: int = Field(..., gt=0)
    preview_pages: int = Field(10, ge=0)
    price: float = Field(0.0, ge=0)
    is_free: bool = False
    language: str = Field("en", min_length=2, max_length=10)
    isbn: Optional[str] = None
    enable_watermark: bool = True
    watermark_text: Optional[str] = None
    tags: Optional[List[str]] = None


class BookCreate(BookBase):
    """Schema for creating a book."""
    pass


class BookUpdate(BaseModel):
    """Schema for updating a book."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    author_name: Optional[str] = Field(None, min_length=1, max_length=255)
    total_pages: Optional[int] = Field(None, gt=0)
    preview_pages: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, ge=0)
    is_free: Optional[bool] = None
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    isbn: Optional[str] = None
    enable_watermark: Optional[bool] = None
    watermark_text: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")
    tags: Optional[List[str]] = None


class BookResponse(BaseModel):
    """Schema for book response."""
    id: str
    title: str
    slug: str
    description: Optional[str]
    author_name: str
    author_id: Optional[str]
    price: float
    is_free: bool
    total_pages: int
    preview_pages: int
    cover_image_url: Optional[str]
    pdf_url: Optional[str]
    epub_url: Optional[str]
    language: str
    isbn: Optional[str]
    status: str
    downloads_count: int
    views_count: int
    average_rating: Optional[float]
    review_count: Optional[int]
    tags: Optional[List[str]]
    published_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class BookListResponse(BaseModel):
    """Schema for paginated book list response."""
    items: List[BookResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class BookSearchParams(BaseModel):
    """Schema for book search parameters."""
    q: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    language: Optional[str] = None
    sort: Optional[str] = Field(None, pattern="^(relevance|newest|price_asc|price_desc|popular)$")
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
