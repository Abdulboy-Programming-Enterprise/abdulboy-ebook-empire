"""
Book Repository
===============
Database operations for book management.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models.book import Book, BookStatus, Tag, BookTag


class BookRepository:
    """Repository for book database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, book_id: str) -> Optional[Book]:
        """Get book by ID."""
        result = await self.db.execute(select(Book).where(Book.id == book_id))
        return result.scalar_one_or_none()
    
    async def get_by_slug(self, slug: str) -> Optional[Book]:
        """Get book by slug."""
        result = await self.db.execute(select(Book).where(Book.slug == slug))
        return result.scalar_one_or_none()
    
    async def create(self, book_data: dict) -> Book:
        """Create a new book."""
        book = Book(**book_data)
        self.db.add(book)
        await self.db.commit()
        await self.db.refresh(book)
        return book
    
    async def update(self, book_id: str, update_data: dict) -> Optional[Book]:
        """Update book information."""
        book = await self.get_by_id(book_id)
        if not book:
            return None
        
        for key, value in update_data.items():
            if hasattr(book, key):
                setattr(book, key, value)
        
        await self.db.commit()
        await self.db.refresh(book)
        return book
    
    async def delete(self, book_id: str) -> bool:
        """Soft delete book."""
        book = await self.get_by_id(book_id)
        if not book:
            return False
        
        from datetime import datetime
        book.deleted_at = datetime.utcnow()
        book.status = BookStatus.ARCHIVED
        await self.db.commit()
        return True
    
    async def publish(self, book_id: str) -> Optional[Book]:
        """Publish a book."""
        book = await self.get_by_id(book_id)
        if not book:
            return None
        
        from datetime import datetime
        book.status = BookStatus.PUBLISHED
        book.published_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(book)
        return book
    
    async def list_books(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[Book], int]:
        """List books with pagination and filtering."""
        query = select(Book).where(Book.deleted_at.is_(None))
        
        if status:
            query = query.where(Book.status == status)
        else:
            query = query.where(Book.status == BookStatus.PUBLISHED)
        
        if search:
            query = query.where(
                or_(
                    Book.title.ilike(f"%{search}%"),
                    Book.author_name.ilike(f"%{search}%")
                )
            )
        
        if category:
            query = query.join(Book.tags).where(Tag.slug == category)
        
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        
        query = query.order_by(Book.published_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await self.db.execute(query)
        books = result.scalars().all()
        
        return books, total or 0
