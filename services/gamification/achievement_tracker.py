"""
Achievement Tracker
===================
Tracks user progress toward achievements and awards them when completed.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.models.achievement import Achievement, UserAchievement
from app.models.user import User
from app.core.logger import logger


class AchievementTracker:
    """Tracks and awards achievements to users."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def update_progress(
        self,
        user_id: str,
        category: str,
        increment: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Update user's progress toward achievements.
        
        Args:
            user_id: User identifier
            category: Achievement category (reading, purchasing, reviewing, streak)
            increment: Amount to increment progress
            
        Returns:
            List of newly completed achievements
        """
        # Get achievements in this category
        result = await self.db.execute(
            select(Achievement).where(
                Achievement.category == category,
                Achievement.is_active == True
            )
        )
        achievements = result.scalars().all()
        
        # Get user's current progress
        user_achievements = {}
        result = await self.db.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        )
        for ua in result:
            user_achievements[ua.achievement_id] = ua
        
        # Get user's current value for this category
        current_value = await self._get_category_value(user_id, category)
        
        completed = []
        
        for achievement in achievements:
            # Check if already completed
            if achievement.id in user_achievements and user_achievements[achievement.id].is_completed:
                continue
            
            # Update progress
            progress = min(100, int((current_value / achievement.target_value) * 100))
            
            if achievement.id in user_achievements:
                ua = user_achievements[achievement.id]
                ua.progress = progress
                ua.updated_at = datetime.utcnow()
            else:
                ua = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    progress=progress,
                    is_completed=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                self.db.add(ua)
            
            # Check if completed
            if progress >= 100 and not ua.is_completed:
                ua.is_completed = True
                ua.completed_at = datetime.utcnow()
                completed.append({
                    "achievement_id": str(achievement.id),
                    "name": achievement.name,
                    "description": achievement.description,
                    "points_awarded": achievement.points_awarded,
                })
                
                # Award points
                if achievement.points_awarded > 0:
                    user_result = await self.db.execute(select(User).where(User.id == user_id))
                    user = user_result.scalar_one()
                    user.total_points += achievement.points_awarded
                
                logger.info(f"User {user_id} completed achievement: {achievement.name}")
        
        await self.db.commit()
        
        return completed
    
    async def _get_category_value(self, user_id: str, category: str) -> int:
        """Get current value for a category."""
        if category == "reading":
            # Count books purchased/read
            from app.models.payment import UserBookPurchase
            result = await self.db.execute(
                select(UserBookPurchase).where(UserBookPurchase.user_id == user_id)
            )
            return len(result.all())
        
        elif category == "purchasing":
            # Count purchases
            from app.models.payment import Payment
            result = await self.db.execute(
                select(Payment).where(
                    Payment.user_id == user_id,
                    Payment.status == "completed"
                )
            )
            return len(result.all())
        
        elif category == "reviewing":
            # Count reviews written
            return 0  # Placeholder
        
        elif category == "streak":
            # Get reading streak
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            return user.reading_streak if user else 0
        
        return 0
    
    async def get_user_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all achievements for a user with progress."""
        result = await self.db.execute(
            select(Achievement).where(Achievement.is_active == True)
        )
        achievements = result.scalars().all()
        
        result = await self.db.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        )
        user_achievements = {ua.achievement_id: ua for ua in result}
        
        response = []
        for achievement in achievements:
            ua = user_achievements.get(achievement.id)
            response.append({
                "id": str(achievement.id),
                "name": achievement.name,
                "description": achievement.description,
                "category": achievement.category,
                "target_value": achievement.target_value,
                "points_awarded": achievement.points_awarded,
                "progress": ua.progress if ua else 0,
                "is_completed": ua.is_completed if ua else False,
                "completed_at": ua.completed_at.isoformat() if ua and ua.completed_at else None,
            })
        
        return response
