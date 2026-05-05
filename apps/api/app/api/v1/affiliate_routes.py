"""
Affiliate Routes
================
Affiliate marketing and referral tracking endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from app.core.database import get_db
from app.models.user import User
from app.models.affiliate import AffiliateLink, AffiliateClick
from app.schemas.response import StandardResponse
from app.api.deps import get_current_user
from app.utils.helpers import generate_id

router = APIRouter(prefix="/affiliate", tags=["Affiliate"])


@router.post("/generate-link")
async def generate_affiliate_link(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate an affiliate link for the current user.
    """
    # Check if user already has a link
    result = await db.execute(
        select(AffiliateLink).where(AffiliateLink.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return StandardResponse(
            success=True,
            data={
                "code": existing.code,
                "link": f"https://abdulboy-ebook.com/?ref={existing.code}",
                "clicks": existing.clicks_count,
                "conversions": existing.conversions_count,
                "earnings": existing.earnings_total,
            }
        )
    
    # Generate new affiliate link
    code = generate_id(prefix="REF")[:12]
    affiliate_link = AffiliateLink(
        user_id=current_user.id,
        code=code,
        commission_rate=0.10,  # 10% commission
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(affiliate_link)
    await db.commit()
    await db.refresh(affiliate_link)
    
    return StandardResponse(
        success=True,
        data={
            "code": affiliate_link.code,
            "link": f"https://abdulboy-ebook.com/?ref={affiliate_link.code}",
            "commission_rate": affiliate_link.commission_rate,
        }
    )


@router.get("/stats")
async def get_affiliate_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get affiliate statistics for current user.
    """
    result = await db.execute(
        select(AffiliateLink).where(AffiliateLink.user_id == current_user.id)
    )
    affiliate_link = result.scalar_one_or_none()
    
    if not affiliate_link:
        raise HTTPException(status_code=404, detail="No affiliate link found")
    
    return StandardResponse(
        success=True,
        data={
            "code": affiliate_link.code,
            "clicks": affiliate_link.clicks_count,
            "conversions": affiliate_link.conversions_count,
            "earnings": affiliate_link.earnings_total,
            "commission_rate": affiliate_link.commission_rate,
        }
    )
