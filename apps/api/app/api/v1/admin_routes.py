"""
Admin Routes
============
Administrative endpoints for platform management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta
from typing import Optional, List
from app.core.database import get_db
from app.models.user import User, AccountType, SubscriptionStatus
from app.models.book import Book, BookStatus
from app.models.payment import Payment, PaymentStatus
from app.models.booking import Booking, BookingStatus
from app.models.audit import AuditLog
from app.schemas.user import UserCreate, UserResponse
from app.schemas.response import StandardResponse
from app.api.deps import get_current_admin_user
from app.core.security import get_password_hash
from app.core.logger import logger
from app.tasks.email_jobs import send_welcome_email

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard/stats", response_model=StandardResponse)
async def get_admin_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get comprehensive dashboard statistics for admin.
    """
    # User statistics
    total_users = await db.scalar(select(func.count()).select_from(User))
    new_users_today = await db.scalar(
        select(func.count()).select_from(User).where(
            User.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        )
    )
    active_subscriptions = await db.scalar(
        select(func.count()).select_from(User).where(
            User.subscription_status.in_([SubscriptionStatus.BASIC, SubscriptionStatus.PREMIUM]),
            User.subscription_ends_at > datetime.utcnow()
        )
    )
    
    # Book statistics
    total_books = await db.scalar(
        select(func.count()).select_from(Book).where(Book.status == BookStatus.PUBLISHED)
    )
    new_books_this_month = await db.scalar(
        select(func.count()).select_from(Book).where(
            Book.status == BookStatus.PUBLISHED,
            Book.published_at >= datetime.utcnow() - timedelta(days=30)
        )
    )
    
    # Payment statistics
    total_revenue = await db.scalar(
        select(func.sum(Payment.amount)).where(Payment.status == PaymentStatus.COMPLETED)
    )
    revenue_this_month = await db.scalar(
        select(func.sum(Payment.amount)).where(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.paid_at >= datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        )
    )
    pending_payments = await db.scalar(
        select(func.count()).select_from(Payment).where(Payment.status == PaymentStatus.PENDING)
    )
    
    # Booking statistics
    pending_bookings = await db.scalar(
        select(func.count()).select_from(Booking).where(Booking.status == BookingStatus.PENDING)
    )
    
    return StandardResponse(
        success=True,
        data={
            "users": {
                "total": total_users or 0,
                "new_today": new_users_today or 0,
                "active_subscriptions": active_subscriptions or 0,
            },
            "books": {
                "total": total_books or 0,
                "new_this_month": new_books_this_month or 0,
            },
            "revenue": {
                "total": float(total_revenue) if total_revenue else 0,
                "this_month": float(revenue_this_month) if revenue_this_month else 0,
            },
            "payments": {
                "pending": pending_payments or 0,
            },
            "bookings": {
                "pending": pending_bookings or 0,
            },
        }
    )


@router.get("/users", response_model=StandardResponse)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    account_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    List all users with pagination and filtering (Admin only).
    """
    query = select(User).where(User.deleted_at.is_(None))
    
    if search:
        query = query.where(
            or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    
    if account_type:
        query = query.where(User.account_type == account_type)
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    
    user_responses = []
    for user in users:
        user_responses.append({
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "account_type": user.account_type.value,
            "subscription_status": user.subscription_status.value,
            "total_points": user.total_points,
            "email_verified": user.email_verified_at is not None,
            "created_at": user.created_at.isoformat(),
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        })
    
    return StandardResponse(
        success=True,
        data={
            "items": user_responses,
            "total": total or 0,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if total else 0,
        }
    )


@router.post("/users", response_model=StandardResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Create a new user (Admin only).
    """
    # Check existing
    result = await db.execute(select(User).where(User.email == user_data.email.lower()))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    new_user = User(
        email=user_data.email.lower(),
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        account_type=AccountType.NORMAL,
        subscription_status=SubscriptionStatus.FREE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    send_welcome_email.delay(
        user_id=str(new_user.id),
        user_email=new_user.email,
        user_name=new_user.full_name
    )
    
    logger.info(f"Admin {current_user.email} created user: {new_user.email}")
    
    return StandardResponse(
        success=True,
        message="User created successfully",
        data={"id": str(new_user.id), "email": new_user.email}
    )


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Update user role (normal, special, admin).
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if role not in ['normal', 'special', 'admin']:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    # Prevent changing own role
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    user.account_type = AccountType(role)
    user.updated_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"Admin {current_user.email} changed role of {user.email} to {role}")
    
    return StandardResponse(success=True, message=f"User role updated to {role}")


@router.post("/users/{user_id}/special")
async def create_special_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Create a special user account (free access to all books).
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.account_type = AccountType.SPECIAL
    user.subscription_status = SubscriptionStatus.PREMIUM
    user.subscription_started_at = datetime.utcnow()
    user.subscription_ends_at = datetime.utcnow() + timedelta(days=365 * 100)  # 100 years
    user.updated_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"Admin {current_user.email} created special user: {user.email}")
    
    return StandardResponse(
        success=True,
        message=f"User {user.email} is now a special user with free access"
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Soft delete a user (Admin only).
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user.deleted_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"Admin {current_user.email} deleted user: {user.email}")
    
    return StandardResponse(success=True, message="User deleted successfully")


@router.get("/audit-logs", response_model=StandardResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    action_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get audit logs of admin actions.
    """
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    
    if action_type:
        query = query.where(AuditLog.action_type == action_type)
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    log_responses = []
    for log in logs:
        log_responses.append({
            "id": str(log.id),
            "admin_email": log.admin_email,
            "action_type": log.action_type,
            "target_type": log.target_type,
            "target_id": str(log.target_id) if log.target_id else None,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "ip_address": str(log.ip_address) if log.ip_address else None,
            "created_at": log.created_at.isoformat(),
        })
    
    return StandardResponse(
        success=True,
        data={
            "items": log_responses,
            "total": total or 0,
            "page": page,
            "limit": limit,
        }
    )


@router.post("/admin-accounts")
async def create_admin_account(
    email: str,
    full_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Create a new admin account.
    """
    result = await db.execute(select(User).where(User.email == email.lower()))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    temp_password = User.create_temp_password()
    
    new_admin = User(
        email=email.lower(),
        password_hash=get_password_hash(temp_password),
        full_name=full_name,
        account_type=AccountType.ADMIN,
        subscription_status=SubscriptionStatus.PREMIUM,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(new_admin)
    await db.commit()
    
    # Send welcome email with temp password
    send_welcome_email.delay(
        user_id=str(new_admin.id),
        user_email=new_admin.email,
        user_name=new_admin.full_name,
        temp_password=temp_password
    )
    
    logger.info(f"Admin {current_user.email} created admin account: {email}")
    
    return StandardResponse(
        success=True,
        message=f"Admin account created. Temporary password sent to {email}"
    )
