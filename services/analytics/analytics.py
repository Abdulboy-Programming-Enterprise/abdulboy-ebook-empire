"""
Analytics Service
=================
Business logic for analytics and reporting.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.models.book import Book, BookStatus
from app.models.analytics import AnalyticsEvent


class AnalyticsService:
    """Service for analytics operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_daily_revenue(self, date: datetime = None) -> float:
        """Get revenue for a specific day."""
        if date is None:
            date = datetime.utcnow()
        
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        result = await self.db.execute(
            select(func.sum(Payment.amount))
            .where(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.paid_at >= start,
                Payment.paid_at < end
            )
        )
        return float(result.scalar() or 0)
    
    async def get_period_revenue(self, start_date: datetime, end_date: datetime = None) -> float:
        """Get revenue for a date period."""
        if end_date is None:
            end_date = datetime.utcnow()
        
        result = await self.db.execute(
            select(func.sum(Payment.amount))
            .where(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.paid_at >= start_date,
                Payment.paid_at <= end_date
            )
        )
        return float(result.scalar() or 0)
    
    async def get_new_users_count(self, since: datetime) -> int:
        """Get number of new users since a date."""
        result = await self.db.execute(
            select(func.count())
            .select_from(User)
            .where(User.created_at >= since)
        )
        return result.scalar() or 0
    
    async def get_total_users(self) -> int:
        """Get total number of users."""
        result = await self.db.execute(select(func.count()).select_from(User))
        return result.scalar() or 0
    
    async def get_active_users_count(self, days: int = 30) -> int:
        """Get number of active users in last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(func.count())
            .select_from(User)
            .where(User.last_login_at >= cutoff)
        )
        return result.scalar() or 0
    
    async def get_new_books_count(self, since: datetime) -> int:
        """Get number of new books published since a date."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Book)
            .where(
                Book.status == BookStatus.PUBLISHED,
                Book.published_at >= since
            )
        )
        return result.scalar() or 0
    
    async def get_top_books(self, limit: int = 10) -> list:
        """Get most popular books by downloads."""
        result = await self.db.execute(
            select(Book)
            .where(Book.status == BookStatus.PUBLISHED)
            .order_by(Book.downloads_count.desc())
            .limit(limit)
        )
        books = result.scalars().all()
        
        return [{
            "id": str(b.id),
            "title": b.title,
            "author": b.author_name,
            "downloads": b.downloads_count,
        } for b in books]
    
    async def get_top_categories(self, limit: int = 5) -> list:
        """Get most popular categories by book count."""
        # This would join with tags table
        # Simplified for now
        return []
    
    async def get_active_subscribers_count(self) -> int:
        """Get number of active subscribers."""
        result = await self.db.execute(
            select(func.count())
            .select_from(User)
            .where(
                User.subscription_status.in_(['basic', 'premium']),
                User.subscription_ends_at > datetime.utcnow()
            )
        )
        return result.scalar() or 0
    
    async def get_user_retention_rate(self) -> float:
        """Calculate user retention rate."""
        # Users who signed up 30 days ago
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        sixty_days_ago = datetime.utcnow() - timedelta(days=60)
        
        # Users who signed up 30-60 days ago
        result = await self.db.execute(
            select(func.count())
            .select_from(User)
            .where(
                User.created_at <= thirty_days_ago,
                User.created_at >= sixty_days_ago
            )
        )
        cohort = result.scalar() or 1
        
        # Users from that cohort who were active in last 30 days
        active_result = await self.db.execute(
            select(func.count())
            .select_from(User)
            .where(
                User.created_at <= thirty_days_ago,
                User.created_at >= sixty_days_ago,
                User.last_login_at >= thirty_days_ago
            )
        )
        active = active_result.scalar() or 0
        
        return (active / cohort) * 100
