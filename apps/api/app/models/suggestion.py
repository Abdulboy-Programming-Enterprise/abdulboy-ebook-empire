"""
Suggestion Model
================
Book recommendation logs and user interaction tracking for AI suggestions.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TimestampMixin


class SuggestionLog(BaseModel, TimestampMixin):
    """Log of book recommendations shown to users."""
    
    __tablename__ = "suggestion_logs"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    
    # Suggestion metadata
    suggestion_type = Column(String(50), nullable=False)  # collaborative, content_based, popular
    confidence_score = Column(Float, default=0.0)
    
    # Interaction tracking
    was_clicked = Column(Boolean, default=False)
    was_purchased = Column(Boolean, default=False)
    clicked_at = Column(DateTime, nullable=True)
    
    # Context
    context = Column(JSON, nullable=True)  # Where suggestion was shown, etc.
    
    # Relationships
    user = relationship("User")
    book = relationship("Book")
    
    __table_args__ = (
        Index('idx_suggestion_user', 'user_id', 'created_at'),
    )
