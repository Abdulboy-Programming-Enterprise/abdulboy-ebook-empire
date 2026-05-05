"""
Leaderboard Service
===================
Manages user leaderboards for points and badges.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
from app.models.user import User
from app.models.badge import UserBadge
from app.core.cache import cache_service


class LeaderboardService:
    """Service for leaderboard management."""
    
    LEADERBOARD_TTL = 3600  # 1 hour cache
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_leaderboard(
        self,
        period: str = "weekly",
        limit: int = 50,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get leaderboard for specified period.
        
        Args:
            period: daily, weekly, monthly, all_time
            limit: Maximum number of entries
            user_id: Optional user ID to highlight
            
        Returns:
            List of leaderboard entries
        """
        # Check cache
        cache_key = f"leaderboard:{period}:{limit}"
        cached = await cache_service.get(cache_key)
        if cached:
            return cached[:limit]
        
        # Build query based on period
        query = select(User.id, User.full_name, User.avatar_url, User.total_points)
        
        if period == "daily":
            # Points earned today (simplified - would need points transaction log)
            pass
        elif period == "weekly":
            # Points earned this week
            pass
        elif period == "monthly":
            # Points earned this month
            pass
        
        # Order by points
        query = query.order_by(desc(User.total_points)).limit(limit)
        
        result = await self.db.execute(query)
        users = result.all()
        
        leaderboard = []
        for rank, (uid, name, avatar, points) in enumerate(users, 1):
            # Get badge count
            badge_result = await self.db.execute(
                select(func.count()).select_from(UserBadge).where(UserBadge.user_id == uid)
            )
            badge_count = badge_result.scalar() or 0
            
            leaderboard.append({
                "rank": rank,
                "user_id": str(uid),
                "user_name": name,
                "user_avatar": avatar,
                "total_points": points,
                "badge_count": badge_count,
            })
        
        # Cache result
        await cache_service.set(cache_key, leaderboard, self.LEADERBOARD_TTL)
        
        return leaderboard
    
    async def get_user_rank(
        self,
        user_id: str,
        period: str = "weekly"
    ) -> Optional[Dict[str, Any]]:
        """
        Get user's rank in leaderboard.
        
        Args:
            user_id: User identifier
            period: Leaderboard period
            
        Returns:
            User rank info or None
        """
        leaderboard = await self.get_leaderboard(period, limit=1000)
        
        for entry in leaderboard:
            if entry["user_id"] == user_id:
                # Get total users count
                total_result = await self.db.execute(select(func.count()).select_from(User))
                total_users = total_result.scalar() or 0
                
                return {
                    "rank": entry["rank"],
                    "total_users": total_users,
                    "total_points": entry["total_points"],
                    "badge_count": entry["badge_count"],
                    "percentile": round((1 - (entry["rank"] - 1) / total_users) * 100, 1) if total_users > 0 else 0,
                }
        
        return None
    
    async def get_top_performers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performers for the current week."""
        return await self.get_leaderboard(period="weekly", limit=limit)
    
    async def invalidate_leaderboard(self):
        """Invalidate leaderboard cache."""
        patterns = ["leaderboard:*"]
        for pattern in patterns:
            await cache_service.delete(pattern)
