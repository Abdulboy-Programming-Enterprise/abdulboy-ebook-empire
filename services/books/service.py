"""
Book Management Service
=======================
High-level service for book management.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from services.books.repository import BookRepository
from services.books.book import BookService
from app.models.book import Book


class BookManagementService:
    """High-level service for book management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = BookRepository(db)
        self.book_service = BookService(self.repository)
    
    async def get_book(self, book_id: str) -> Optional[Book]:
        """Get book by ID."""
        return await self.repository.get_by_id(book_id)
    
    async def get_book_by_slug(self, slug: str) -> Optional[Book]:
        """Get book by slug."""
        return await self.repository.get_by_slug(slug)
    
    async def create_book(self, book_data: dict) -> dict:
        """Create a new book."""
        return await self.book_service.create_book(book_data)
    
    async def update_book(self, book_id: str, update_data: dict) -> Optional[dict]:
        """Update a book."""
        return await self.book_service.update_book(book_id, update_data)
    
    async def publish_book(self, book_id: str) -> Optional[dict]:
        """Publish a book."""
        return await self.book_service.publish_book(book_id)
    
    async def delete_book(self, book_id: str) -> bool:
        """Soft delete book."""
        return await self.repository.delete(book_id)
    
    async def list_books(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[Book], int]:
        """List books with pagination."""
        return await self.repository.list_books(page, limit, status, category, search)
    
    async def increment_view_count(self, book_id: str) -> None:
        """Increment book view count."""
        book = await self.repository.get_by_id(book_id)
        if book:
            book.views_count += 1
            await self.db.commit()
