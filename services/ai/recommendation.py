"""
Recommendation Service
======================
AI-powered book recommendation engine.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.book import Book, BookStatus
from app.models.payment import UserBookPurchase
from app.core.logger import logger


class RecommendationService:
    """Service for AI-powered book recommendations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_recommendations(
        self,
        user_id: str,
        limit: int = 10,
        exclude_purchased: bool = True
    ) -> List[Book]:
        """Get personalized recommendations for a user."""
        # Get user's purchased books
        purchased_book_ids = []
        if exclude_purchased:
            result = await self.db.execute(
                select(UserBookPurchase.book_id)
                .where(UserBookPurchase.user_id == user_id)
            )
            purchased_book_ids = [row[0] for row in result.all()]
        
        # Simple popularity-based recommendation for MVP
        query = select(Book).where(
            Book.status == BookStatus.PUBLISHED,
            Book.deleted_at.is_(None)
        )
        
        if exclude_purchased and purchased_book_ids:
            query = query.where(Book.id.not_in(purchased_book_ids))
        
        query = query.order_by(
            (Book.downloads_count + Book.views_count * 0.1).desc()
        ).limit(limit)
        
        result = await self.db.execute(query)
        books = result.scalars().all()
        
        logger.info(f"Generated {len(books)} recommendations for user {user_id}")
        
        return books
    
    async def get_similar_books(
        self,
        book_id: str,
        limit: int = 10
    ) -> List[Book]:
        """Get books similar to a given book."""
        # Get source book
        result = await self.db.execute(select(Book).where(Book.id == book_id))
        source_book = result.scalar_one_or_none()
        
        if not source_book:
            return []
        
        # Simple similarity based on tags/category
        # For MVP, return other books by same author or popular books
        query = select(Book).where(
            Book.status == BookStatus.PUBLISHED,
            Book.deleted_at.is_(None),
            Book.id != book_id
        )
        
        # Prioritize same author
        query = query.order_by(
            (Book.author_name == source_book.author_name).desc(),
            Book.downloads_count.desc()
        ).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_popular_books(
        self,
        limit: int = 10,
        days: int = 30
    ) -> List[Book]:
        """Get most popular books from the last N days."""
        from datetime import datetime, timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        query = select(Book).where(
            Book.status == BookStatus.PUBLISHED,
            Book.deleted_at.is_(None),
            Book.published_at >= cutoff
        ).order_by(
            Book.downloads_count.desc()
        ).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
