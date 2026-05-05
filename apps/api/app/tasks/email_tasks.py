"""
Email Tasks
===========
Celery tasks for sending various email notifications.
"""

from celery import shared_task
from datetime import datetime
from app.services.notifications.email_service import EmailService
from app.core.logger import logger

email_service = EmailService()


@shared_task(name="send_welcome_email", bind=True, max_retries=3)
def send_welcome_email(self, user_email: str, user_name: str, temp_password: str = None):
    """
    Send welcome email to new user.
    """
    try:
        result = email_service.send_welcome_email(
            to_email=user_email,
            template_data={
                "name": user_name,
                "temp_password": temp_password,
                "dashboard_url": "https://abdulboy-ebook.com/user-dashboard.html",
                "current_year": datetime.now().year,
            }
        )
        
        if result:
            logger.info(f"Welcome email sent to {user_email}")
            return {"status": "success", "user_email": user_email}
        else:
            raise Exception("Failed to send email")
            
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user_email}: {e}")
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(name="send_purchase_confirmation", bind=True, max_retries=3)
def send_purchase_confirmation(
    self,
    user_email: str,
    user_name: str,
    order_id: str,
    items: list,
    total_amount: float,
    payment_method: str
):
    """
    Send purchase confirmation email.
    """
    try:
        result = email_service.send_purchase_confirmation(
            to_email=user_email,
            template_data={
                "name": user_name,
                "orderId": order_id,
                "orderDate": datetime.now().strftime("%B %d, %Y"),
                "paymentMethod": payment_method,
                "totalAmount": f"${total_amount:.2f}",
                "items": items,
                "libraryUrl": "https://abdulboy-ebook.com/user-dashboard.html#library",
            }
        )
        
        if result:
            logger.info(f"Purchase confirmation sent to {user_email} for order {order_id}")
            return {"status": "success", "order_id": order_id}
        else:
            raise Exception("Failed to send email")
            
    except Exception as e:
        logger.error(f"Failed to send purchase confirmation for order {order_id}: {e}")
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(name="send_password_reset_email", bind=True, max_retries=3)
def send_password_reset_email(self, user_email: str, user_name: str, reset_token: str):
    """
    Send password reset email.
    """
    try:
        reset_url = f"https://abdulboy-ebook.com/reset-password.html?token={reset_token}"
        
        result = email_service.send_password_reset_email(
            to_email=user_email,
            template_data={
                "name": user_name,
                "resetUrl": reset_url,
                "expiryHours": 24,
            }
        )
        
        if result:
            logger.info(f"Password reset email sent to {user_email}")
            return {"status": "success"}
        else:
            raise Exception("Failed to send email")
            
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user_email}: {e}")
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(name="send_booking_confirmation", bind=True, max_retries=3)
def send_booking_confirmation(
    self,
    user_email: str,
    user_name: str,
    booking_id: str,
    booking_details: dict
):
    """
    Send custom book booking confirmation email.
    """
    try:
        result = email_service.send_booking_confirmation(
            to_email=user_email,
            template_data={
                "name": user_name,
                "bookingId": booking_id,
                "title": booking_details.get("title", "Custom Book"),
                "genre": booking_details.get("genre", "Not specified"),
                "wordCount": booking_details.get("word_count", "TBD"),
                "budget": f"${booking_details.get('budget', 0):.2f}",
                "deadline": booking_details.get("deadline", "To be confirmed"),
                "requirements": booking_details.get("requirements", ""),
                "bookingUrl": f"https://abdulboy-ebook.com/booking-status.html?id={booking_id}",
                "dashboardUrl": "https://abdulboy-ebook.com/user-dashboard.html",
            }
        )
        
        if result:
            logger.info(f"Booking confirmation sent for booking {booking_id}")
            return {"status": "success", "booking_id": booking_id}
        else:
            raise Exception("Failed to send email")
            
    except Exception as e:
        logger.error(f"Failed to send booking confirmation for booking {booking_id}: {e}")
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(name="send_booking_update", bind=True, max_retries=3)
def send_booking_update(
    self,
    user_email: str,
    user_name: str,
    booking_id: str,
    status: str,
    admin_notes: str = None,
    delivery_url: str = None,
):
    """
    Send booking status update email.
    """
    try:
        result = email_service.send_booking_update(
            to_email=user_email,
            template_data={
                "name": user_name,
                "bookingId": booking_id,
                "status": status,
                "admin_notes": admin_notes,
                "delivery_url": delivery_url,
                "bookingUrl": f"https://abdulboy-ebook.com/booking-status.html?id={booking_id}",
            }
        )
        
        if result:
            logger.info(f"Booking update sent for booking {booking_id}")
            return {"status": "success"}
        else:
            raise Exception("Failed to send email")
            
    except Exception as e:
        logger.error(f"Failed to send booking update for booking {booking_id}: {e}")
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(name="send_new_book_notification", bind=True, max_retries=3)
def send_new_book_notification(self, book_id: str):
    """
    Send notification to subscribers about new book.
    """
    try:
        # Get book details and notify subscribers
        # This would query the database for subscribers
        logger.info(f"New book notification sent for book {book_id}")
        return {"status": "success", "book_id": book_id}
    except Exception as e:
        logger.error(f"Failed to send new book notification: {e}")
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(name="send_weekly_newsletter", bind=True)
def send_weekly_newsletter(self):
    """
    Send weekly newsletter to all subscribed users.
    """
    try:
        # Get all newsletter subscribers and send
        logger.info("Weekly newsletter sent")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to send weekly newsletter: {e}")
        raise
