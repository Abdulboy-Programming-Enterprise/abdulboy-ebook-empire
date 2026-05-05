"""
Book Service
============
Business logic for book operations.
"""

from typing import Optional
from services.books.repository import BookRepository
from app.utils.helpers import generate_slug


class BookService:
    """Service for book business logic."""
    
    def __init__(self, repository: BookRepository):
        self.repository = repository
    
    async def create_book(self, book_data: dict) -> dict:
        """Create a new book."""
        # Generate slug if not provided
        if not book_data.get("slug"):
            book_data["slug"] = generate_slug(book_data["title"])
        
        # Check slug uniqueness
        existing = await self.repository.get_by_slug(book_data["slug"])
        if existing:
            book_data["slug"] = f"{book_data['slug']}-{generate_slug(str(datetime.now()))[:8]}"
        
        book = await self.repository.create(book_data)
        return {
            "id": str(book.id),
            "title": book.title,
            "slug": book.slug,
        }
    
    async def update_book(self, book_id: str, update_data: dict) -> Optional[dict]:
        """Update a book."""
        book = await self.repository.update(book_id, update_data)
        if not book:
            return None
        
        return {
            "id": str(book.id),
            "title": book.title,
            "slug": book.slug,
        }
    
    async def publish_book(self, book_id: str) -> Optional[dict]:
        """Publish a book."""
        book = await self.repository.publish(book_id)
        if not book:
            return None
        
        return {
            "id": str(book.id),
            "title": book.title,
            "published_at": book.published_at.isoformat() if book.published_at else None,
        }
    
    async def get_book_details(self, book_id: str) -> Optional[dict]:
        """Get detailed book information."""
        book = await self.repository.get_by_id(book_id)
        if not book:
            return None
        
        return {
            "id": str(book.id),
            "title": book.title,
            "slug": book.slug,
            "description": book.description,
            "author_name": book.author_name,
            "price": book.price,
            "is_free": book.is_free,
            "total_pages": book.total_pages,
            "cover_image_url": book.cover_image_url,
            "language": book.language,
            "isbn": book.isbn,
            "status": book.status.value,
            "downloads_count": book.downloads_count,
            "views_count": book.views_count,
            "published_at": book.published_at.isoformat() if book.published_at else None,
            "created_at": book.created_at.isoformat(),
        }
