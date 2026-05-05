"""
Booking Service
===============
Service for managing custom book booking requests.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from app.models.booking import Booking, BookingStatus
from app.core.logger import logger


class BookingService:
    """Service for custom book booking operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_booking(
        self,
        user_id: str,
        title: str,
        description: Optional[str],
        genre: Optional[str],
        word_count: Optional[int],
        deadline: Optional[datetime],
        budget: Optional[float],
        requirements: Optional[str]
    ) -> Booking:
        """Create a new custom book booking."""
        booking = Booking(
            user_id=user_id,
            title=title,
            description=description,
            genre=genre,
            word_count=word_count,
            deadline=deadline,
            budget=budget,
            requirements=requirements,
            status=BookingStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        self.db.add(booking)
        await self.db.commit()
        await self.db.refresh(booking)
        
        logger.info(f"Booking created: {booking.id} - {title}")
        
        return booking
    
    async def get_booking(self, booking_id: str) -> Optional[Booking]:
        """Get booking by ID."""
        result = await self.db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_bookings(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Booking], int]:
        """Get bookings for a specific user."""
        query = select(Booking).where(Booking.user_id == user_id)
        
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        
        query = query.order_by(Booking.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await self.db.execute(query)
        bookings = result.scalars().all()
        
        return bookings, total or 0
    
    async def get_all_bookings(
        self,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Booking], int]:
        """Get all bookings (admin only)."""
        query = select(Booking)
        
        if status:
            query = query.where(Booking.status == status)
        
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        
        query = query.order_by(Booking.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await self.db.execute(query)
        bookings = result.scalars().all()
        
        return bookings, total or 0
    
    async def update_booking_status(
        self,
        booking_id: str,
        status: str,
        admin_notes: Optional[str] = None,
        delivery_url: Optional[str] = None
    ) -> Optional[Booking]:
        """Update booking status (admin only)."""
        booking = await self.get_booking(booking_id)
        
        if not booking:
            return None
        
        booking.status = BookingStatus(status)
        booking.updated_at = datetime.utcnow()
        
        if admin_notes:
            booking.admin_notes = admin_notes
        
        if status == "accepted":
            booking.accepted_at = datetime.utcnow()
        elif status == "completed":
            booking.completed_at = datetime.utcnow()
        elif status == "delivered" and delivery_url:
            booking.delivery_url = delivery_url
            booking.delivered_at = datetime.utcnow()
        elif status == "cancelled":
            booking.cancelled_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        logger.info(f"Booking {booking_id} status updated to {status}")
        
        return booking
    
    async def cancel_booking(self, booking_id: str, user_id: str) -> bool:
        """Cancel a booking (user or admin)."""
        booking = await self.get_booking(booking_id)
        
        if not booking:
            return False
        
        if booking.user_id != user_id:
            return False
        
        if booking.status not in [BookingStatus.PENDING, BookingStatus.ACCEPTED]:
            return False
        
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        booking.updated_at = datetime.utcnow()
        await self.db.commit()
        
        logger.info(f"Booking {booking_id} cancelled by user {user_id}")
        
        return True
    
    async def deliver_booking(
        self,
        booking_id: str,
        delivery_url: str,
        admin_notes: Optional[str] = None
    ) -> Optional[Booking]:
        """Deliver completed booking."""
        booking = await self.get_booking(booking_id)
        
        if not booking:
            return None
        
        if booking.status != BookingStatus.COMPLETED:
            return None
        
        booking.status = BookingStatus.DELIVERED
        booking.delivery_url = delivery_url
        booking.delivered_at = datetime.utcnow()
        booking.updated_at = datetime.utcnow()
        
        if admin_notes:
            booking.admin_notes = admin_notes
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        logger.info(f"Booking {booking_id} delivered")
        
        return booking
