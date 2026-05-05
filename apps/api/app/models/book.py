"""
Book Model
==========
Book, Tag, and BookTag models for the ebook catalog.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel, TimestampMixin


class BookStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Book(BaseModel, TimestampMixin):
    """Book model for ebook catalog."""
    
    __tablename__ = "books"
    
    title = Column(String(500), nullable=False)
    slug = Column(String(500), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    author_name = Column(String(255), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Pricing
    price = Column(Float, default=0.0)
    is_free = Column(Boolean, default=False)
    
    # Preview settings
    total_pages = Column(Integer, nullable=False)
    preview_pages = Column(Integer, default=10)
    preview_content = Column(Text, nullable=True)
    
    # File references
    pdf_url = Column(String(500), nullable=True)
    epub_url = Column(String(500), nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    
    # Metadata
    isbn = Column(String(20), nullable=True)
    language = Column(String(10), default="en")
    publication_date = Column(DateTime, nullable=True)
    
    # Watermarking
    enable_watermark = Column(Boolean, default=True)
    watermark_text = Column(String(255), nullable=True)
    
    # Status
    status = Column(Enum(BookStatus), default=BookStatus.DRAFT)
    downloads_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    
    # Search vector (PostgreSQL full-text search)
    search_vector = Column(Text, nullable=True)
    
    # Published timestamp
    published_at = Column(DateTime, nullable=True)
    
    # Soft delete
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    author = relationship("User", foreign_keys=[author_id])
    purchases = relationship("UserBookPurchase", back_populates="book", cascade="all, delete-orphan")
    tags = relationship("BookTag", back_populates="book", cascade="all, delete-orphan")
    reading_activities = relationship("ReadingActivity", back_populates="book", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_books_search', 'search_vector', postgresql_using='gin'),
        Index('idx_books_status_published', 'status', 'published_at'),
    )
    
    @property
    def is_published(self) -> bool:
        return self.status == BookStatus.PUBLISHED
    
    def __repr__(self):
        return f"<Book {self.title}>"


class Tag(BaseModel, TimestampMixin):
    """Tag model for categorizing books."""
    
    __tablename__ = "tags"
    
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    
    # Relationships
    books = relationship("BookTag", back_populates="tag", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tag {self.name}>"


class BookTag(BaseModel):
    """Association table for Book-Tag many-to-many relationship."""
    
    __tablename__ = "book_tags"
    
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    
    # Relationships
    book = relationship("Book", back_populates="tags")
    tag = relationship("Tag", back_populates="books")
