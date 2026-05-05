"""
Badge Model
============
Gamification badges and user earned badges.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel, TimestampMixin


class BadgeRarity(str, enum.Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class BadgeCriteriaType(str, enum.Enum):
    BOOKS_READ = "books_read"
    REVIEWS_WRITTEN = "reviews_written"
    PURCHASE_COUNT = "purchase_count"
    STREAK_DAYS = "streak_days"
    TOTAL_POINTS = "total_points"
    SPECIAL = "special"


class Badge(BaseModel, TimestampMixin):
    """Badge definition model for gamification."""
    
    __tablename__ = "badges"
    
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    
    # Badge criteria
    criteria_type = Column(String(50), nullable=False)
    criteria_value = Column(Integer, nullable=False)
    
    # Points awarded
    points = Column(Integer, default=100)
    
    rarity = Column(String(20), default=BadgeRarity.COMMON)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user_badges = relationship("UserBadge", back_populates="badge", cascade="all, delete-orphan")


class UserBadge(BaseModel):
    """User earned badges."""
    
    __tablename__ = "user_badges"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    badge_id = Column(UUID(as_uuid=True), ForeignKey("badges.id", ondelete="CASCADE"), primary_key=True)
    
    earned_at = Column(DateTime, default=datetime.utcnow)
    progress = Column(Integer, default=100)  # Percentage progress toward badge
    
    # Relationships
    user = relationship("User", back_populates="badges")
    badge = relationship("Badge", back_populates="user_badges")
