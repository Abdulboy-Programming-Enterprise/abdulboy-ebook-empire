"""
Challenge Manager
=================
Manages daily and weekly challenges for users.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from app.core.cache import cache_service
from app.core.logger import logger


class ChallengeManager:
    """Manages daily and weekly challenges for users."""
    
    # Challenge definitions
    CHALLENGES = {
        "daily": [
            {
                "id": "daily_read",
                "name": "Daily Reader",
                "description": "Read for 15 minutes today",
                "goal": 15,
                "unit": "minutes",
                "points_reward": 50,
            },
            {
                "id": "daily_login",
                "name": "Daily Visitor",
                "description": "Log in to your account",
                "goal": 1,
                "unit": "login",
                "points_reward": 10,
            },
            {
                "id": "daily_search",
                "name": "Curious Mind",
                "description": "Search for books 3 times",
                "goal": 3,
                "unit": "searches",
                "points_reward": 20,
            },
        ],
        "weekly": [
            {
                "id": "weekly_read",
                "name": "Avid Reader",
                "description": "Read 3 books this week",
                "goal": 3,
                "unit": "books",
                "points_reward": 300,
                "badge_reward": "avid_reader",
            },
            {
                "id": "weekly_review",
                "name": "Helpful Reviewer",
                "description": "Write 5 book reviews",
                "goal": 5,
                "unit": "reviews",
                "points_reward": 250,
                "badge_reward": "helpful_reviewer",
            },
            {
                "id": "weekly_streak",
                "name": "Streak Master",
                "description": "Maintain a 7-day reading streak",
                "goal": 7,
                "unit": "days",
                "points_reward": 500,
                "badge_reward": "streak_master",
            },
        ],
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_progress = {}  # In production, store in Redis/DB
    
    async def get_active_challenges(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get active challenges for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of active challenges with progress
        """
        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday())
        
        challenges = []
        
        # Daily challenges
        daily_key = f"challenge:daily:{user_id}:{today.isoformat()}"
        daily_progress = await cache_service.get(daily_key) or {}
        
        for challenge in self.CHALLENGES["daily"]:
            progress = daily_progress.get(challenge["id"], 0)
            challenges.append({
                **challenge,
                "type": "daily",
                "progress": progress,
                "is_completed": progress >= challenge["goal"],
                "expires_at": (datetime.utcnow() + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat(),
            })
        
        # Weekly challenges
        weekly_key = f"challenge:weekly:{user_id}:{week_start.isoformat()}"
        weekly_progress = await cache_service.get(weekly_key) or {}
        
        for challenge in self.CHALLENGES["weekly"]:
            progress = weekly_progress.get(challenge["id"], 0)
            challenges.append({
                **challenge,
                "type": "weekly",
                "progress": progress,
                "is_completed": progress >= challenge["goal"],
                "expires_at": (week_start + timedelta(days=7)).isoformat(),
            })
        
        return challenges
    
    async def update_progress(
        self,
        user_id: str,
        challenge_id: str,
        increment: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Update progress for a challenge.
        
        Args:
            user_id: User identifier
            challenge_id: Challenge identifier
            increment: Amount to increment
            
        Returns:
            Updated challenge info or None if completed
        """
        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday())
        
        # Check daily challenges
        for challenge in self.CHALLENGES["daily"]:
            if challenge["id"] == challenge_id:
                key = f"challenge:daily:{user_id}:{today.isoformat()}"
                progress = await cache_service.get(key) or {}
                new_progress = progress.get(challenge_id, 0) + increment
                progress[challenge_id] = new_progress
                await cache_service.set(key, progress, 86400)  # 24 hours
                
                if new_progress >= challenge["goal"] and progress.get(challenge_id, 0) < challenge["goal"]:
                    # Challenge completed!
                    logger.info(f"User {user_id} completed daily challenge: {challenge['name']}")
                    return {
                        "completed": True,
                        "challenge": challenge,
                        "points_awarded": challenge["points_reward"],
                    }
                
                return {
                    "completed": False,
                    "challenge": challenge,
                    "progress": new_progress,
                    "goal": challenge["goal"],
                }
        
        # Check weekly challenges
        for challenge in self.CHALLENGES["weekly"]:
            if challenge["id"] == challenge_id:
                key = f"challenge:weekly:{user_id}:{week_start.isoformat()}"
                progress = await cache_service.get(key) or {}
                new_progress = progress.get(challenge_id, 0) + increment
                progress[challenge_id] = new_progress
                await cache_service.set(key, progress, 604800)  # 7 days
                
                if new_progress >= challenge["goal"] and progress.get(challenge_id, 0) < challenge["goal"]:
                    # Challenge completed!
                    logger.info(f"User {user_id} completed weekly challenge: {challenge['name']}")
                    return {
                        "completed": True,
                        "challenge": challenge,
                        "points_awarded": challenge["points_reward"],
                    }
                
                return {
                    "completed": False,
                    "challenge": challenge,
                    "progress": new_progress,
                    "goal": challenge["goal"],
                }
        
        return None
    
    async def award_challenge_rewards(
        self,
        user_id: str,
        challenge: Dict[str, Any],
        points_system
    ) -> bool:
        """Award rewards for completed challenge."""
        try:
            # Award points
            await points_system.award_points(
                user_id=user_id,
                points=challenge["points_reward"],
                reason=f"Completed {challenge['name']} challenge"
            )
            
            # Award badge if applicable
            if "badge_reward" in challenge:
                # Award badge logic here
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to award challenge rewards: {e}")
            return False
