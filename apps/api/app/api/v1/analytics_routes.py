"""
Analytics Routes
================
Analytics and reporting endpoints for platform insights.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from datetime import datetime, timedelta
from typing import Optional
from app.core.database import get_db
from app.models.user import User
from app.models.payment import Payment, PaymentStatus
from app.models.book import Book, BookStatus
from app.models.analytics import AnalyticsEvent
from app.schemas.response import StandardResponse
from app.api.deps import get_current_admin_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=StandardResponse)
async def get_analytics_dashboard(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get comprehensive analytics dashboard data (Admin only).
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Revenue over time
    revenue_result = await db.execute(
        select(
            func.date(Payment.paid_at).label("date"),
            func.sum(Payment.amount).label("revenue")
        )
        .where(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.paid_at >= start_date
        )
        .group_by(func.date(Payment.paid_at))
        .order_by(func.date(Payment.paid_at))
    )
    revenue_over_time = [
        {"date": str(row.date), "revenue": float(row.revenue)}
        for row in revenue_result
    ]
    
    # User registrations over time
    users_result = await db.execute(
        select(
            func.date(User.created_at).label("date"),
            func.count().label("count")
        )
        .where(User.created_at >= start_date)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    registrations_over_time = [
        {"date": str(row.date), "count": row.count}
        for row in users_result
    ]
    
    # Book sales
    books_sold = await db.scalar(
        select(func.count())
        .select_from(Payment)
        .where(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.item_type == "book",
            Payment.paid_at >= start_date
        )
    ) or 0
    
    # New books published
    new_books = await db.scalar(
        select(func.count())
        .select_from(Book)
        .where(
            Book.status == BookStatus.PUBLISHED,
            Book.published_at >= start_date
        )
    ) or 0
    
    # Active users (logged in within last 30 days)
    active_users = await db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.last_login_at >= end_date - timedelta(days=30))
    ) or 0
    
    return StandardResponse(
        success=True,
        data={
            "period_days": days,
            "revenue": {
                "total": sum(r["revenue"] for r in revenue_over_time),
                "over_time": revenue_over_time,
            },
            "users": {
                "total": await db.scalar(select(func.count()).select_from(User)) or 0,
                "new": sum(r["count"] for r in registrations_over_time),
                "registrations_over_time": registrations_over_time,
                "active": active_users,
            },
            "books": {
                "sold": books_sold,
                "new_published": new_books,
                "total": await db.scalar(select(func.count()).select_from(Book).where(Book.status == BookStatus.PUBLISHED)) or 0,
            },
        }
    )


@router.get("/revenue", response_model=StandardResponse)
async def get_revenue_analytics(
    period: str = Query("month", regex="^(day|week|month|year)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get detailed revenue analytics.
    """
    now = datetime.utcnow()
    
    if period == "day":
        start_date = now - timedelta(days=30)
        group_by = func.date(Payment.paid_at)
    elif period == "week":
        start_date = now - timedelta(weeks=52)
        group_by = extract('week', Payment.paid_at)
    elif period == "month":
        start_date = now - timedelta(days=365)
        group_by = func.date_trunc('month', Payment.paid_at)
    else:
        start_date = now - timedelta(days=365*3)
        group_by = func.date_trunc('year', Payment.paid_at)
    
    revenue_result = await db.execute(
        select(
            group_by.label("period"),
            func.sum(Payment.amount).label("revenue"),
            func.count().label("transactions")
        )
        .where(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.paid_at >= start_date
        )
        .group_by(group_by)
        .order_by(group_by)
    )
    
    revenue_data = [
        {"period": str(row.period), "revenue": float(row.revenue), "transactions": row.transactions}
        for row in revenue_result
    ]
    
    # By payment method
    method_result = await db.execute(
        select(
            Payment.payment_method,
            func.sum(Payment.amount).label("revenue"),
            func.count().label("count")
        )
        .where(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.paid_at >= start_date
        )
        .group_by(Payment.payment_method)
    )
    
    by_method = [
        {"method": row.payment_method, "revenue": float(row.revenue), "count": row.count}
        for row in method_result
    ]
    
    return StandardResponse(
        success=True,
        data={
            "period": period,
            "over_time": revenue_data,
            "by_payment_method": by_method,
        }
    )


@router.get("/users", response_model=StandardResponse)
async def get_user_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get user analytics and engagement metrics.
    """
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    
    # User counts by type
    admin_count = await db.scalar(select(func.count()).select_from(User).where(User.account_type == "admin")) or 0
    special_count = await db.scalar(select(func.count()).select_from(User).where(User.account_type == "special")) or 0
    normal_count = await db.scalar(select(func.count()).select_from(User).where(User.account_type == "normal")) or 0
    
    # Subscription distribution
    free_users = await db.scalar(select(func.count()).select_from(User).where(User.subscription_status == "free")) or 0
    basic_users = await db.scalar(select(func.count()).select_from(User).where(User.subscription_status == "basic")) or 0
    premium_users = await db.scalar(select(func.count()).select_from(User).where(User.subscription_status == "premium")) or 0
    
    # Retention (users who logged in within last 30 days)
    active_users = await db.scalar(
        select(func.count()).select_from(User).where(User.last_login_at >= thirty_days_ago)
    ) or 0
    total_users = await db.scalar(select(func.count()).select_from(User)) or 1
    retention_rate = (active_users / total_users) * 100
    
    return StandardResponse(
        success=True,
        data={
            "total_users": total_users,
            "by_type": {
                "admin": admin_count,
                "special": special_count,
                "normal": normal_count,
            },
            "by_subscription": {
                "free": free_users,
                "basic": basic_users,
                "premium": premium_users,
            },
            "engagement": {
                "active_users_30d": active_users,
                "retention_rate": round(retention_rate, 2),
            }
        }
    )
