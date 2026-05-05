"""
Gamification Schemas
=====================
Pydantic schemas for gamification features.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class LeaderboardEntry(BaseModel):
    """Schema for leaderboard entry."""
    user_id: str
    user_name: str
    user_avatar: Optional[str]
    total_points: int
    rank: int
    badges_count: int


class LeaderboardResponse(BaseModel):
    """Schema for leaderboard response."""
    entries: List[LeaderboardEntry]
    user_rank: Optional[LeaderboardEntry] = None
    total_users: int
    period: str  # daily, weekly, monthly, all_time


class PointsTransaction(BaseModel):
    """Schema for points transaction."""
    id: str
    user_id: str
    points: int
    reason: str
    metadata: Optional[dict]
    created_at: datetime


class Challenge(BaseModel):
    """Schema for daily/weekly challenge."""
    id: str
    name: str
    description: str
    goal: int
    progress: int
    points_reward: int
    badge_reward: Optional[str]
    starts_at: datetime
    ends_at: datetime
    is_completed: bool


class ChallengeResponse(BaseModel):
    """Schema for challenge response."""
    active_challenges: List[Challenge]
    completed_challenges: List[Challenge]
    total_points_earned: int
    total_badges_earned: int


class PointAwardRequest(BaseModel):
    """Schema for awarding points."""
    user_id: str
    points: int = Field(..., gt=0)
    reason: str
    metadata: Optional[dict] = None
