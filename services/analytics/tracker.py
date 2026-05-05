"""
Analytics Tracker
=================
Event tracking for user behavior and system analytics.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid
from app.models.analytics import AnalyticsEvent
from app.core.logger import logger


class AnalyticsTracker:
    """Service for tracking analytics events."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def track_event(
        self,
        user_id: str,
        event_type: str,
        event_data: dict = None,
        session_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        referrer: str = None
    ) -> str:
        """Track an analytics event."""
        event = AnalyticsEvent(
            user_id=user_id,
            event_type=event_type,
            event_data=event_data,
            session_id=session_id or str(uuid.uuid4()),
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            created_at=datetime.utcnow(),
        )
        
        self.db.add(event)
        await self.db.commit()
        
        logger.debug(f"Tracked event: {event_type} for user {user_id}")
        
        return str(event.id)
    
    async def track_page_view(
        self,
        user_id: str,
        page: str,
        session_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> str:
        """Track page view event."""
        return await self.track_event(
            user_id=user_id,
            event_type="page_view",
            event_data={"page": page},
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    async def track_book_view(
        self,
        user_id: str,
        book_id: str,
        book_title: str,
        session_id: str = None
    ) -> str:
        """Track book view event."""
        return await self.track_event(
            user_id=user_id,
            event_type="book_view",
            event_data={"book_id": book_id, "book_title": book_title},
            session_id=session_id,
        )
    
    async def track_search(
        self,
        user_id: str,
        query: str,
        results_count: int,
        session_id: str = None
    ) -> str:
        """Track search event."""
        return await self.track_event(
            user_id=user_id,
            event_type="search",
            event_data={"query": query, "results_count": results_count},
            session_id=session_id,
        )
    
    async def track_purchase(
        self,
        user_id: str,
        amount: float,
        item_type: str,
        item_id: str,
        session_id: str = None
    ) -> str:
        """Track purchase event."""
        return await self.track_event(
            user_id=user_id,
            event_type="purchase",
            event_data={
                "amount": amount,
                "item_type": item_type,
                "item_id": item_id
            },
            session_id=session_id,
        )
