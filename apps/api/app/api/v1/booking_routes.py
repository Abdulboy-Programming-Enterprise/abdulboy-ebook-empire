"""
Booking Routes
==============
Custom book booking management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Optional
from app.core.database import get_db
from app.models.user import User
from app.models.booking import Booking, BookingStatus
from app.schemas.booking import BookingCreate, BookingUpdate, BookingResponse
from app.schemas.response import StandardResponse
from app.api.deps import get_current_user, get_current_admin_user
from app.core.logger import logger
from app.tasks.email_jobs import send_booking_confirmation, send_booking_update

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/", response_model=StandardResponse)
async def create_booking(
    booking_data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a custom book booking request.
    """
    new_booking = Booking(
        user_id=current_user.id,
        title=booking_data.title,
        description=booking_data.description,
        genre=booking_data.genre,
        word_count=booking_data.word_count,
        deadline=booking_data.deadline,
        budget=booking_data.budget,
        requirements=booking_data.requirements,
        status=BookingStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(new_booking)
    await db.commit()
    await db.refresh(new_booking)
    
    # Send confirmation email
    send_booking_confirmation.delay(
        user_email=current_user.email,
        user_name=current_user.full_name,
        booking_id=str(new_booking.id),
        booking_details={
            "title": new_booking.title,
            "genre": new_booking.genre,
            "word_count": new_booking.word_count,
            "budget": new_booking.budget,
            "deadline": new_booking.deadline.isoformat() if new_booking.deadline else None,
            "requirements": new_booking.requirements,
        }
    )
    
    logger.info(f"User {current_user.email} created booking: {new_booking.id}")
    
    return StandardResponse(
        success=True,
        message="Booking request submitted successfully",
        data={
            "id": str(new_booking.id),
            "status": new_booking.status.value,
            "created_at": new_booking.created_at.isoformat(),
        }
    )


@router.get("/", response_model=StandardResponse)
async def get_user_bookings(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's custom book bookings.
    """
    query = select(Booking).where(
        Booking.user_id == current_user.id
    ).order_by(Booking.created_at.desc())
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    bookings = result.scalars().all()
    
    booking_responses = []
    for booking in bookings:
        booking_responses.append({
            "id": str(booking.id),
            "title": booking.title,
            "description": booking.description,
            "genre": booking.genre,
            "word_count": booking.word_count,
            "budget": booking.budget,
            "deadline": booking.deadline.isoformat() if booking.deadline else None,
            "status": booking.status.value,
            "created_at": booking.created_at.isoformat(),
            "updated_at": booking.updated_at.isoformat(),
        })
    
    return StandardResponse(
        success=True,
        data={
            "items": booking_responses,
            "total": total or 0,
            "page": page,
            "limit": limit,
        }
    )


@router.get("/{booking_id}", response_model=StandardResponse)
async def get_booking_details(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get details of a specific booking.
    """
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return StandardResponse(
        success=True,
        data={
            "id": str(booking.id),
            "title": booking.title,
            "description": booking.description,
            "genre": booking.genre,
            "word_count": booking.word_count,
            "deadline": booking.deadline.isoformat() if booking.deadline else None,
            "budget": booking.budget,
            "requirements": booking.requirements,
            "status": booking.status.value,
            "admin_notes": booking.admin_notes,
            "delivery_url": booking.delivery_url,
            "created_at": booking.created_at.isoformat(),
            "updated_at": booking.updated_at.isoformat(),
        }
    )


@router.put("/{booking_id}")
async def update_booking(
    booking_id: str,
    booking_data: BookingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a booking (user can update pending bookings).
    """
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(status_code=400, detail="Cannot update booking after it's been accepted")
    
    update_data = booking_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)
    
    booking.updated_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"User {current_user.email} updated booking {booking_id}")
    
    return StandardResponse(
        success=True,
        message="Booking updated successfully"
    )


@router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cancel a pending booking.
    """
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if booking.status not in [BookingStatus.PENDING, BookingStatus.ACCEPTED]:
        raise HTTPException(status_code=400, detail="Cannot cancel booking at this stage")
    
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.utcnow()
    booking.updated_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"Booking {booking_id} cancelled by {current_user.email}")
    
    return StandardResponse(
        success=True,
        message="Booking cancelled successfully"
    )


# Admin endpoints
@router.get("/admin/all", response_model=StandardResponse)
async def admin_get_all_bookings(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get all bookings (Admin only).
    """
    query = select(Booking).order_by(Booking.created_at.desc())
    
    if status:
        query = query.where(Booking.status == status)
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    bookings = result.scalars().all()
    
    booking_responses = []
    for booking in bookings:
        # Get user info
        user_result = await db.execute(select(User).where(User.id == booking.user_id))
        user = user_result.scalar_one_or_none()
        
        booking_responses.append({
            "id": str(booking.id),
            "user": {
                "id": str(user.id) if user else None,
                "email": user.email if user else None,
                "full_name": user.full_name if user else None,
            },
            "title": booking.title,
            "budget": booking.budget,
            "status": booking.status.value,
            "created_at": booking.created_at.isoformat(),
        })
    
    return StandardResponse(
        success=True,
        data={
            "items": booking_responses,
            "total": total or 0,
            "page": page,
            "limit": limit,
        }
    )


@router.put("/admin/{booking_id}/status")
async def admin_update_booking_status(
    booking_id: str,
    status: str,
    admin_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Update booking status (Admin only).
    """
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    valid_statuses = [s.value for s in BookingStatus]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    booking.status = BookingStatus(status)
    if admin_notes:
        booking.admin_notes = admin_notes
    
    if status == "accepted":
        booking.accepted_at = datetime.utcnow()
    elif status == "completed":
        booking.completed_at = datetime.utcnow()
    elif status == "delivered":
        booking.delivered_at = datetime.utcnow()
    
    booking.updated_at = datetime.utcnow()
    await db.commit()
    
    # Send update email
    user_result = await db.execute(select(User).where(User.id == booking.user_id))
    user = user_result.scalar_one()
    
    send_booking_update.delay(
        user_email=user.email,
        user_name=user.full_name,
        booking_id=str(booking.id),
        status=status,
        admin_notes=admin_notes,
    )
    
    logger.info(f"Admin {current_user.email} updated booking {booking_id} status to {status}")
    
    return StandardResponse(
        success=True,
        message=f"Booking status updated to {status}"
    )


@router.post("/admin/{booking_id}/deliver")
async def deliver_booking(
    booking_id: str,
    delivery_url: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Deliver completed custom book (Admin only).
    """
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.status != BookingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Booking must be completed before delivery")
    
    booking.status = BookingStatus.DELIVERED
    booking.delivery_url = delivery_url
    booking.delivered_at = datetime.utcnow()
    booking.updated_at = datetime.utcnow()
    await db.commit()
    
    # Send delivery notification
    user_result = await db.execute(select(User).where(User.id == booking.user_id))
    user = user_result.scalar_one()
    
    send_booking_update.delay(
        user_email=user.email,
        user_name=user.full_name,
        booking_id=str(booking.id),
        status="delivered",
        delivery_url=delivery_url,
    )
    
    logger.info(f"Admin {current_user.email} delivered booking {booking_id}")
    
    return StandardResponse(
        success=True,
        message="Booking delivered successfully"
    )
