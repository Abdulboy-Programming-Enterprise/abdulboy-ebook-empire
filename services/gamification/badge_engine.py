"""
Badge Engine
============
Awards badges to users based on achievements and criteria.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from app.models.badge import Badge, UserBadge, BadgeCriteriaType
from app.models.user import User
from app.core.logger import logger


class BadgeEngine:
    """Engine for awarding badges based on user actions."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_and_award_badges(
        self,
        user_id: str,
        event_type: str,
        event_data: Dict[str, Any] = None
    ) -> List[Badge]:
        """
        Check conditions and award badges to user.
        
        Args:
            user_id: User identifier
            event_type: Type of event (books_read, reviews_written, etc.)
            event_data: Additional event data
            
        Returns:
            List of newly awarded badges
        """
        # Get user data for criteria checking
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return []
        
        # Get user stats
        stats = await self._get_user_stats(user_id)
        
        # Get all active badges
        result = await self.db.execute(select(Badge).where(Badge.is_active == True))
        all_badges = result.scalars().all()
        
        # Get badges user already has
        result = await self.db.execute(
            select(UserBadge.badge_id).where(UserBadge.user_id == user_id)
        )
        earned_badge_ids = {row[0] for row in result.all()}
        
        new_badges = []
        
        for badge in all_badges:
            if badge.id in earned_badge_ids:
                continue
            
            # Check if user meets criteria
            meets_criteria = await self._check_criteria(
                badge, stats, event_type, event_data
            )
            
            if meets_criteria:
                # Award badge
                user_badge = UserBadge(
                    user_id=user_id,
                    badge_id=badge.id,
                    earned_at=datetime.utcnow(),
                    progress=100
                )
                self.db.add(user_badge)
                
                # Award points
                if badge.points > 0:
                    user.total_points += badge.points
                
                new_badges.append(badge)
                logger.info(f"User {user_id} earned badge: {badge.name}")
        
        if new_badges:
            await self.db.commit()
        
        return new_badges
    
    async def _get_user_stats(self, user_id: str) -> Dict[str, int]:
        """Get user statistics for badge criteria checking."""
        # Get books read count
        from app.models.payment import UserBookPurchase
        books_result = await self.db.execute(
            select(UserBookPurchase)
            .where(UserBookPurchase.user_id == user_id)
        )
        books_read = len(books_result.all())
        
        # Get reviews written count (placeholder - would query reviews table)
        reviews_written = 0
        
        # Get purchase count
        from app.models.payment import Payment
        purchases_result = await self.db.execute(
            select(Payment)
            .where(
                Payment.user_id == user_id,
                Payment.status == "completed"
            )
        )
        purchase_count = len(purchases_result.all())
        
        # Get user for streak and points
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        return {
            "books_read": books_read,
            "reviews_written": reviews_written,
            "purchase_count": purchase_count,
            "reading_streak": user.reading_streak if user else 0,
            "total_points": user.total_points if user else 0,
        }
    
    async def _check_criteria(
        self,
        badge: Badge,
        stats: Dict[str, int],
        event_type: str,
        event_data: Dict[str, Any]
    ) -> bool:
        """Check if user meets badge criteria."""
        if badge.criteria_type == BadgeCriteriaType.BOOKS_READ.value:
            return stats.get("books_read", 0) >= badge.criteria_value
        
        elif badge.criteria_type == BadgeCriteriaType.REVIEWS_WRITTEN.value:
            return stats.get("reviews_written", 0) >= badge.criteria_value
        
        elif badge.criteria_type == BadgeCriteriaType.PURCHASE_COUNT.value:
            return stats.get("purchase_count", 0) >= badge.criteria_value
        
        elif badge.criteria_type == BadgeCriteriaType.STREAK_DAYS.value:
            return stats.get("reading_streak", 0) >= badge.criteria_value
        
        elif badge.criteria_type == BadgeCriteriaType.TOTAL_POINTS.value:
            return stats.get("total_points", 0) >= badge.criteria_value
        
        elif badge.criteria_type == "special":
            # Special badges require manual awarding
            return False
        
        return False
    
    async def get_user_badges(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all badges earned by a user."""
        result = await self.db.execute(
            select(UserBadge, Badge)
            .join(Badge, UserBadge.badge_id == Badge.id)
            .where(UserBadge.user_id == user_id)
            .order_by(UserBadge.earned_at.desc())
        )
        
        badges = []
        for user_badge, badge in result:
            badges.append({
                "badge_id": str(badge.id),
                "name": badge.name,
                "slug": badge.slug,
                "description": badge.description,
                "image_url": badge.image_url,
                "points": badge.points,
                "rarity": badge.rarity,
                "earned_at": user_badge.earned_at.isoformat(),
            })
        
        return badges
