"""
Analytics Model
===============
Analytics event tracking for user behavior and system metrics.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class EventType(str, enum.Enum):
    PAGE_VIEW = "page_view"
    BOOK_VIEW = "book_view"
    SEARCH = "search"
    LOGIN = "login"
    PURCHASE = "purchase"


class AnalyticsEvent(BaseModel):
    """Analytics event model for tracking user behavior."""
    
    __tablename__ = "analytics_events"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    event_type = Column(String(50), nullable=False)
    event_data = Column(JSON, nullable=True)
    
    session_id = Column(UUID(as_uuid=True), nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    referrer = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_analytics_user_time', 'user_id', 'created_at'),
        Index('idx_analytics_type_time', 'event_type', 'created_at'),
    )
