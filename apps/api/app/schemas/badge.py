"""
Badge Schemas
==============
Pydantic schemas for badge-related operations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BadgeCriteria(BaseModel):
    """Badge criteria schema."""
    criteria_type: str
    criteria_value: int


class BadgeResponse(BaseModel):
    """Schema for badge response."""
    id: str
    name: str
    slug: str
    description: Optional[str]
    image_url: Optional[str]
    points: int
    rarity: str
    criteria_type: str
    criteria_value: int
    
    class Config:
        from_attributes = True


class UserBadgeResponse(BaseModel):
    """Schema for user badge response."""
    badge_id: str
    badge_name: str
    badge_image: Optional[str]
    points: int
    rarity: str
    earned_at: datetime
    progress: int
    
    class Config:
        from_attributes = True


class BadgeCheckResponse(BaseModel):
    """Schema for badge check response."""
    earned: bool
    badge: Optional[BadgeResponse] = None
    progress_current: int
    progress_target: int
    percent_complete: float
