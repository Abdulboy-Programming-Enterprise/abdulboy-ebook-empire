"""
Point System
============
Manages user points for purchases, reading, reviews, and daily activities.
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.models.user import User
from app.core.logger import logger


class PointSystem:
    """System for awarding points to users."""
    
    # Point multipliers
    POINTS_CONFIG = {
        'purchase': 10,           # 10 points per dollar spent
        'review': 50,             # 50 points per review
        'daily_login': 10,        # 10 points for daily login
        'book_completed': 100,    # 100 points for finishing a book
        'streak_bonus': 50,       # 50 points bonus for 7-day streak
        'referral': 200,          # 200 points for referring a friend
        'custom_booking': 500,    # 500 points for custom book order
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def award_points(
        self,
        user_id: str,
        points: int,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Award points to a user.
        
        Args:
            user_id: User identifier
            points: Number of points to award
            reason: Reason for awarding points
            metadata: Additional metadata
            
        Returns:
            New total points
        """
        # Get user
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"User {user_id} not found for point award")
            return 0
        
        # Award points
        user.total_points += points
        await self.db.commit()
        
        # Log point award (would go to audit table)
        logger.info(f"Awarded {points} points to user {user_id} for {reason}")
        
        return user.total_points
    
    async def award_purchase_points(self, user_id: str, amount: float) -> int:
        """
        Award points for a purchase.
        
        Args:
            user_id: User identifier
            amount: Purchase amount in dollars
            
        Returns:
            Points awarded
        """
        points = int(amount * self.POINTS_CONFIG['purchase'])
        return await self.award_points(
            user_id=user_id,
            points=points,
            reason=f"Purchase of ${amount:.2f}"
        )
    
    async def award_review_points(self, user_id: str) -> int:
        """Award points for writing a review."""
        return await self.award_points(
            user_id=user_id,
            points=self.POINTS_CONFIG['review'],
            reason="Wrote a book review"
        )
    
    async def award_daily_login_points(self, user_id: str) -> Optional[int]:
        """
        Award points for daily login (once per day).
        
        Args:
            user_id: User identifier
            
        Returns:
            Points awarded or None if already awarded today
        """
        # Check if already awarded today
        # In production, track last_login_point_award date
        return await self.award_points(
            user_id=user_id,
            points=self.POINTS_CONFIG['daily_login'],
            reason="Daily login bonus"
        )
    
    async def award_streak_bonus(self, user_id: str, streak_days: int) -> Optional[int]:
        """Award bonus points for reading streak milestones."""
        if streak_days >= 7 and streak_days % 7 == 0:
            return await self.award_points(
                user_id=user_id,
                points=self.POINTS_CONFIG['streak_bonus'],
                reason=f"{streak_days}-day reading streak bonus"
            )
        return None
    
    async def get_user_points(self, user_id: str) -> int:
        """Get total points for a user."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user.total_points if user else 0
    
    async def get_leaderboard_rank(self, user_id: str) -> Optional[int]:
        """Get user's rank in the leaderboard."""
        result = await self.db.execute(
            select(User.id, User.total_points)
            .order_by(User.total_points.desc())
        )
        users = result.all()
        
        for rank, (uid, _) in enumerate(users, 1):
            if str(uid) == user_id:
                return rank
        
        return None
