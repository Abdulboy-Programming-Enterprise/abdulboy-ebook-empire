"""
Notification Service
====================
Service for managing user notifications (in-app and push).
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from datetime import datetime
from app.models.notification import Notification, NotificationType


class NotificationService:
    """Service for managing user notifications."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """Create a new notification for a user."""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            metadata=metadata,
            is_read=False,
            created_at=datetime.utcnow(),
        )
        
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        
        return notification
    
    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Notification], int]:
        """Get notifications for a user."""
        query = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            query = query.where(Notification.is_read == False)
        
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        
        query = query.order_by(Notification.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await self.db.execute(query)
        notifications = result.scalars().all()
        
        return notifications, total or 0
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        notification = result.scalar_one_or_none()
        
        if not notification:
            return False
        
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        await self.db.commit()
        
        return True
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user."""
        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        await self.db.commit()
        
        return result.rowcount
    
    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        notification = result.scalar_one_or_none()
        
        if not notification:
            return False
        
        await self.db.delete(notification)
        await self.db.commit()
        
        return True
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get unread notification count for a user."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        return result.scalar() or 0
    
    async def send_welcome_notification(self, user_id: str, user_name: str) -> Notification:
        """Send welcome notification to new user."""
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.WELCOME.value,
            title="Welcome to Abdulboy Ebook Empire! 🎉",
            message=f"Hi {user_name}! Welcome to our community. Start exploring thousands of books and enjoy your reading journey.",
            metadata={"action": "explore_books", "url": "/ebook-site.html"}
        )
    
    async def send_purchase_notification(
        self,
        user_id: str,
        book_title: str,
        amount: float
    ) -> Notification:
        """Send purchase confirmation notification."""
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.PAYMENT.value,
            title="Purchase Confirmed! ✅",
            message=f"You have successfully purchased '{book_title}' for ${amount:.2f}. It's now available in your library.",
            metadata={"action": "view_library", "url": "/user-dashboard.html#library"}
        )
    
    async def send_subscription_notification(
        self,
        user_id: str,
        plan_name: str,
        expires_at: datetime
    ) -> Notification:
        """Send subscription activation notification."""
        days_left = (expires_at - datetime.utcnow()).days
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.SUBSCRIPTION.value,
            title="Subscription Activated! 🎉",
            message=f"Your {plan_name} plan is now active. Enjoy unlimited access to all books! Your subscription will renew in {days_left} days.",
            metadata={"action": "view_books", "url": "/ebook-site.html"}
        )
    
    async def send_booking_notification(
        self,
        user_id: str,
        booking_id: str,
        title: str,
        status: str
    ) -> Notification:
        """Send booking status notification."""
        status_messages = {
            "pending": "Your custom book request has been received and is pending review.",
            "accepted": "Good news! Your custom book request has been accepted and is now in progress.",
            "completed": "Your custom book is complete! Check your email for the download link.",
            "delivered": "Your custom book has been delivered. You can now download it from your dashboard."
        }
        
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.BOOKING.value,
            title=f"Custom Book Update: {title}",
            message=status_messages.get(status, f"Your booking {booking_id} status has been updated to {status}."),
            metadata={"action": "view_booking", "url": f"/booking-status.html?id={booking_id}"}
        )
    
    async def send_gamification_notification(
        self,
        user_id: str,
        badge_name: str,
        points: int
    ) -> Notification:
        """Send badge earned notification."""
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.GAMIFICATION.value,
            title="🏆 Badge Unlocked!",
            message=f"Congratulations! You've earned the '{badge_name}' badge and {points} points.",
            metadata={"action": "view_badges", "url": "/user-dashboard.html#badges"}
        )
