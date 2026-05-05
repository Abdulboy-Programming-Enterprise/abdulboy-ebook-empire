"""
Notification Model
==================
User notifications for system events, purchases, and updates.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TimestampMixin


class NotificationType(str, enum.Enum):
    WELCOME = "welcome"
    NEW_BOOK = "new_book"
    SUBSCRIPTION = "subscription"
    PAYMENT = "payment"
    BOOKING = "booking"
    SYSTEM = "system"
    BOOKING_UPDATE = "booking_update"
    GAMIFICATION = "gamification"


class Notification(BaseModel, TimestampMixin):
    """User notification model."""
    
    __tablename__ = "notifications"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    metadata = Column(JSON, nullable=True)  # Additional data like book_id, booking_id, etc.
    
    # Relationships
    user = relationship("User", back_populates="notifications")
