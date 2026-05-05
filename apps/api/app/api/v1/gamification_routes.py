"""
Gamification Routes
===================
Badges, points, leaderboards, and achievement endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import get_db
from app.models.user import User
from app.models.badge import Badge, UserBadge
from app.models.achievement import Achievement, UserAchievement
from app.schemas.badge import BadgeResponse, UserBadgeResponse
from app.schemas.gamification import LeaderboardEntry, LeaderboardResponse
from app.schemas.response import StandardResponse
from app.api.deps import get_current_user
from app.services.gamification.badge_engine import check_and_award_badges
from app.services.gamification.point_system import PointSystem
from app.services.gamification.leaderboard_service import LeaderboardService
from app.core.logger import logger

router = APIRouter(prefix="/gamification", tags=["Gamification"])


@router.get("/badges", response_model=StandardResponse)
async def get_all_badges(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all available badges with user's earned status.
    """
    # Get all badges
    result = await db.execute(select(Badge).where(Badge.is_active == True))
    all_badges = result.scalars().all()
    
    # Get user's earned badges
    user_badge_result = await db.execute(
        select(UserBadge.badge_id).where(UserBadge.user_id == current_user.id)
    )
    earned_badge_ids = {str(row[0]) for row in user_badge_result}
    
    badge_responses = []
    for badge in all_badges:
        badge_responses.append({
            "id": str(badge.id),
            "name": badge.name,
            "slug": badge.slug,
            "description": badge.description,
            "image_url": badge.image_url,
            "points": badge.points,
            "rarity": badge.rarity,
            "earned": str(badge.id) in earned_badge_ids,
            "criteria_type": badge.criteria_type,
            "criteria_value": badge.criteria_value,
        })
    
    return StandardResponse(
        success=True,
        data={
            "badges": badge_responses,
            "earned_count": len(earned_badge_ids),
            "total_count": len(all_badges),
        }
    )


@router.get("/badges/me", response_model=StandardResponse)
async def get_my_badges(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get badges earned by the current user.
    """
    result = await db.execute(
        select(UserBadge, Badge)
        .join(Badge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.user_id == current_user.id)
        .order_by(UserBadge.earned_at.desc())
    )
    user_badges = result.all()
    
    badge_responses = []
    for user_badge, badge in user_badges:
        badge_responses.append({
            "badge_id": str(badge.id),
            "badge_name": badge.name,
            "badge_image": badge.image_url,
            "points": badge.points,
            "rarity": badge.rarity,
            "earned_at": user_badge.earned_at.isoformat(),
            "progress": user_badge.progress,
        })
    
    return StandardResponse(
        success=True,
        data={
            "badges": badge_responses,
            "total_points": current_user.total_points,
        }
    )


@router.get("/leaderboard", response_model=StandardResponse)
async def get_leaderboard(
    period: str = Query("weekly", regex="^(daily|weekly|monthly|all_time)$"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user leaderboard based on points.
    """
    leaderboard_service = LeaderboardService(db)
    
    entries = await leaderboard_service.get_leaderboard(period=period, limit=limit)
    
    # Find current user's rank
    user_rank = None
    for i, entry in enumerate(entries):
        if entry.user_id == str(current_user.id):
            user_rank = LeaderboardEntry(
                user_id=entry.user_id,
                user_name=entry.user_name,
                user_avatar=entry.user_avatar,
                total_points=entry.total_points,
                rank=i + 1,
                badges_count=entry.badges_count,
            )
            break
    
    return StandardResponse(
        success=True,
        data={
            "entries": [e.dict() for e in entries],
            "user_rank": user_rank.dict() if user_rank else None,
            "total_users": await db.scalar(select(func.count()).select_from(User)) or 0,
            "period": period,
        }
    )


@router.get("/achievements", response_model=StandardResponse)
async def get_achievements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's achievement progress.
    """
    # Get all achievements
    result = await db.execute(select(Achievement).where(Achievement.is_active == True))
    achievements = result.scalars().all()
    
    # Get user's progress
    user_progress_result = await db.execute(
        select(UserAchievement).where(UserAchievement.user_id == current_user.id)
    )
    user_progress = {str(ua.achievement_id): ua for ua in user_progress_result}
    
    achievement_responses = []
    for ach in achievements:
        progress = user_progress.get(str(ach.id))
        achievement_responses.append({
            "id": str(ach.id),
            "name": ach.name,
            "description": ach.description,
            "category": ach.category,
            "target_value": ach.target_value,
            "points_awarded": ach.points_awarded,
            "progress": progress.progress if progress else 0,
            "is_completed": progress.is_completed if progress else False,
            "completed_at": progress.completed_at.isoformat() if progress and progress.completed_at else None,
        })
    
    return StandardResponse(
        success=True,
        data={
            "achievements": achievement_responses,
            "completed_count": sum(1 for a in achievement_responses if a["is_completed"]),
            "total_points_earned": current_user.total_points,
        }
    )


@router.post("/check-badges")
async def check_user_badges(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger badge check for current user.
    """
    new_badges = await check_and_award_badges(str(current_user.id), db)
    
    if new_badges:
        logger.info(f"User {current_user.email} earned {len(new_badges)} new badges")
    
    return StandardResponse(
        success=True,
        message=f"Awarded {len(new_badges)} new badges",
        data={"new_badges": [b.dict() for b in new_badges]}
    )


@router.post("/award-points")
async def award_points_to_user(
    points: int,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Award points to current user (for activities like reading, reviewing).
    """
    point_system = PointSystem(db)
    new_total = await point_system.award_points(
        user_id=str(current_user.id),
        points=points,
        reason=reason,
    )
    
    # Check for new badges
    await check_and_award_badges(str(current_user.id), db)
    
    return StandardResponse(
        success=True,
        message=f"Awarded {points} points for {reason}",
        data={"new_total": new_total}
    )
