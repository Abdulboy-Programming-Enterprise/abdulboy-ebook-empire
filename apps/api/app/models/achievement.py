"""
Achievement Model
=================
User achievements and progress tracking for gamification.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, TimestampMixin


class Achievement(BaseModel, TimestampMixin):
    """Achievement definition model."""
    
    __tablename__ = "achievements"
    
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Achievement type and target
    category = Column(String(50), nullable=False)  # reading, purchasing, reviewing, streak
    target_value = Column(Integer, nullable=False)
    
    # Rewards
    points_awarded = Column(Integer, default=50)
    badge_id = Column(UUID(as_uuid=True), ForeignKey("badges.id"), nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")
    badge = relationship("Badge")


class UserAchievement(BaseModel):
    """User progress toward achievements."""
    
    __tablename__ = "user_achievements"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), primary_key=True)
    
    progress = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")
    achievement = relationship("Achievement", back_populates="user_achievements")
