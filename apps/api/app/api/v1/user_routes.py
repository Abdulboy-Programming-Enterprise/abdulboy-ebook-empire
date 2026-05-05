"""
User Routes
===========
User profile management and dashboard endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime
from typing import Optional
from app.core.database import get_db
from app.models.user import User
from app.models.payment import UserBookPurchase
from app.models.book import Book
from app.models.notification import Notification
from app.models.reading_activity import ReadingActivity
from app.schemas.user import UserUpdate, UserResponse
from app.schemas.response import StandardResponse
from app.api.deps import get_current_user
from app.core.security import get_password_hash, verify_password
from app.core.logger import logger
from app.services.gamification.badge_engine import check_and_award_badges

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=StandardResponse[UserResponse])
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's profile information.
    """
    return StandardResponse(
        success=True,
        data=UserResponse(
            id=str(current_user.id),
            email=current_user.email,
            full_name=current_user.full_name,
            account_type=current_user.account_type.value,
            subscription_status=current_user.subscription_status.value,
            total_points=current_user.total_points,
            reading_streak=current_user.reading_streak,
            email_verified=current_user.email_verified_at is not None,
            created_at=current_user.created_at,
        )
    )


@router.put("/me", response_model=StandardResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update current user's profile information.
    """
    update_data = user_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "password":
            current_user.password_hash = get_password_hash(value)
        else:
            setattr(current_user, field, value)
    
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"User {current_user.email} updated profile")
    
    return StandardResponse(
        success=True,
        message="Profile updated successfully"
    )


@router.get("/me/library", response_model=StandardResponse)
async def get_user_library(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get books purchased by the user.
    """
    query = (
        select(Book)
        .join(UserBookPurchase, UserBookPurchase.book_id == Book.id)
        .where(UserBookPurchase.user_id == current_user.id)
        .order_by(UserBookPurchase.purchased_at.desc())
    )
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    books = result.scalars().all()
    
    book_responses = []
    for book in books:
        # Get purchase info
        purchase_result = await db.execute(
            select(UserBookPurchase).where(
                UserBookPurchase.user_id == current_user.id,
                UserBookPurchase.book_id == book.id
            )
        )
        purchase = purchase_result.scalar_one()
        
        book_responses.append({
            "id": str(book.id),
            "title": book.title,
            "author_name": book.author_name,
            "cover_image_url": book.cover_image_url,
            "purchased_at": purchase.purchased_at.isoformat() if purchase.purchased_at else None,
            "last_accessed_at": purchase.last_accessed_at.isoformat() if purchase.last_accessed_at else None,
            "access_count": purchase.access_count,
        })
    
    return StandardResponse(
        success=True,
        data={
            "items": book_responses,
            "total": total or 0,
            "page": page,
            "limit": limit,
        }
    )


@router.get("/me/notifications", response_model=StandardResponse)
async def get_user_notifications(
    unread_only: bool = False,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user notifications.
    """
    query = select(Notification).where(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.where(Notification.is_read == False)
    
    query = query.order_by(Notification.created_at.desc())
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    notification_responses = []
    for notif in notifications:
        notification_responses.append({
            "id": str(notif.id),
            "type": notif.type,
            "title": notif.title,
            "message": notif.message,
            "is_read": notif.is_read,
            "created_at": notif.created_at.isoformat(),
        })
    
    return StandardResponse(
        success=True,
        data={
            "items": notification_responses,
            "total": total or 0,
            "unread_count": sum(1 for n in notification_responses if not n["is_read"]),
        }
    )


@router.post("/me/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark a notification as read.
    """
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    await db.commit()
    
    return StandardResponse(success=True, message="Marked as read")


@router.post("/me/notifications/read-all")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark all user notifications as read.
    """
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
    )
    notifications = result.scalars().all()
    
    for notif in notifications:
        notif.is_read = True
        notif.read_at = datetime.utcnow()
    
    await db.commit()
    
    return StandardResponse(
        success=True,
        message=f"Marked {len(notifications)} notifications as read"
    )


@router.get("/me/reading-progress", response_model=StandardResponse)
async def get_reading_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's reading progress across books.
    """
    result = await db.execute(
        select(ReadingActivity)
        .where(ReadingActivity.user_id == current_user.id)
        .order_by(ReadingActivity.last_accessed.desc())
        .limit(5)
    )
    activities = result.scalars().all()
    
    progress_data = []
    for activity in activities:
        # Get book details
        book_result = await db.execute(select(Book).where(Book.id == activity.book_id))
        book = book_result.scalar_one_or_none()
        
        if book:
            progress_percent = (activity.last_position / book.total_pages * 100) if book.total_pages > 0 else 0
            
            progress_data.append({
                "id": str(book.id),
                "title": book.title,
                "author": book.author_name,
                "cover_image": book.cover_image_url,
                "progress": round(progress_percent),
                "last_position": activity.last_position,
                "last_accessed": activity.last_accessed.isoformat() if activity.last_accessed else None,
            })
    
    return StandardResponse(
        success=True,
        data={"progress": progress_data}
    )


@router.post("/me/reading-progress/{book_id}")
async def update_reading_progress(
    book_id: str,
    position: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update reading position for a book.
    """
    # Check if user owns the book
    purchase_result = await db.execute(
        select(UserBookPurchase).where(
            UserBookPurchase.user_id == current_user.id,
            UserBookPurchase.book_id == book_id
        )
    )
    purchase = purchase_result.scalar_one_or_none()
    
    if not purchase and not current_user.has_active_subscription and not current_user.is_special:
        raise HTTPException(status_code=403, detail="You don't have access to this book")
    
    # Update or create reading activity
    result = await db.execute(
        select(ReadingActivity).where(
            ReadingActivity.user_id == current_user.id,
            ReadingActivity.book_id == book_id
        )
    )
    activity = result.scalar_one_or_none()
    
    if activity:
        activity.last_position = position
        activity.last_accessed = datetime.utcnow()
        activity.total_time_seconds += 60  # Assume 1 minute of reading
    else:
        activity = ReadingActivity(
            user_id=current_user.id,
            book_id=book_id,
            last_position=position,
            last_accessed=datetime.utcnow(),
            total_time_seconds=0,
        )
        db.add(activity)
    
    # Update purchase access count
    if purchase:
        purchase.access_count += 1
        purchase.last_accessed_at = datetime.utcnow()
    
    await db.commit()
    
    # Check for badge achievements
    await check_and_award_badges(str(current_user.id), db)
    
    return StandardResponse(
        success=True,
        message="Progress updated",
        data={"position": position}
    )


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload user avatar image.
    """
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Validate file size (max 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
    
    # Upload to S3 (simplified - store URL)
    avatar_url = f"/uploads/avatars/{current_user.id}.jpg"
    
    current_user.avatar_url = avatar_url
    await db.commit()
    
    # In production, save file to S3 or local storage
    # with open(f"storage/uploads/user-avatars/{current_user.id}.jpg", "wb") as f:
    #     f.write(contents)
    
    return StandardResponse(
        success=True,
        message="Avatar uploaded successfully",
        data={"avatar_url": avatar_url}
    )
