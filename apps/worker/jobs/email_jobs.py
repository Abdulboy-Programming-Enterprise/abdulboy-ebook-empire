"""
Email Jobs
==========
Background tasks for sending emails (welcome, confirmations, newsletters, etc.)
"""

import logging
from celery import shared_task
from datetime import datetime, timedelta
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


@shared_task(name='email_jobs.send_welcome_email', bind=True, max_retries=3)
def send_welcome_email(self, user_id: int, user_email: str, user_name: str):
    """
    Send welcome email to new user.
    
    Args:
        user_id: Database ID of the user
        user_email: User's email address
        user_name: User's full name
    """
    try:
        logger.info(f'Sending welcome email to {user_email}')
        
        # Import here to avoid circular imports
        from apps.api.app.services.email_service import EmailService
        
        email_service = EmailService()
        result = email_service.send_welcome_email(
            to_email=user_email,
            template_data={
                'name': user_name,
                'user_id': user_id,
                'dashboard_url': 'https://abdulboy-ebook.com/user-dashboard.html',
                'current_year': datetime.now().year,
            }
        )
        
        if result:
            logger.info(f'Welcome email sent to {user_email}')
            return {'status': 'success', 'user_id': user_id}
        else:
            raise Exception('Failed to send email')
            
    except Exception as e:
        logger.error(f'Failed to send welcome email to {user_email}: {e}')
        # Retry with exponential backoff
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(name='email_jobs.send_purchase_confirmation', bind=True, max_retries=3)
def send_purchase_confirmation(
    self,
    user_email: str,
    user_name: str,
    order_id: str,
    items: List[Dict[str, Any]],
    total_amount: float,
    payment_method: str
):
    """
    Send purchase confirmation email.
    
    Args:
        user_email: User's email address
        user_name: User's full name
        order_id: Order identifier
        items: List of purchased items
        total_amount: Total purchase amount
        payment_method: Payment method used
    """
    try:
        logger.info(f'Sending purchase confirmation to {user_email} for order {order_id}')
        
        from apps.api.app.services.email_service import EmailService
        
        email_service = EmailService()
        result = email_service.send_purchase_confirmation(
            to_email=user_email,
            template_data={
                'name': user_name,
                'orderId': order_id,
                'orderDate': datetime.now().strftime('%B %d, %Y'),
                'paymentMethod': payment_method,
                'totalAmount': f'${total_amount:.2f}',
                'items': items,
                'libraryUrl': 'https://abdulboy-ebook.com/user-dashboard.html#library',
            }
        )
        
        if result:
            logger.info(f'Purchase confirmation sent for order {order_id}')
            return {'status': 'success', 'order_id': order_id}
        else:
            raise Exception('Failed to send email')
            
    except Exception as e:
        logger.error(f'Failed to send purchase confirmation for order {order_id}: {e}')
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(name='email_jobs.send_password_reset_email', bind=True, max_retries=3)
def send_password_reset_email(
    self,
    user_email: str,
    user_name: str,
    reset_token: str,
    expiry_hours: int = 24
):
    """
    Send password reset email.
    
    Args:
        user_email: User's email address
        user_name: User's full name
        reset_token: Password reset token
        expiry_hours: Token expiry time in hours
    """
    try:
        logger.info(f'Sending password reset email to {user_email}')
        
        from apps.api.app.services.email_service import EmailService
        
        reset_url = f'https://abdulboy-ebook.com/reset-password.html?token={reset_token}'
        
        email_service = EmailService()
        result = email_service.send_password_reset_email(
            to_email=user_email,
            template_data={
                'name': user_name,
                'resetUrl': reset_url,
                'expiryHours': expiry_hours,
            }
        )
        
        if result:
            logger.info(f'Password reset email sent to {user_email}')
            return {'status': 'success', 'user_email': user_email}
        else:
            raise Exception('Failed to send email')
            
    except Exception as e:
        logger.error(f'Failed to send password reset email to {user_email}: {e}')
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(name='email_jobs.send_booking_confirmation', bind=True, max_retries=3)
def send_booking_confirmation(
    self,
    user_email: str,
    user_name: str,
    booking_id: str,
    booking_details: Dict[str, Any]
):
    """
    Send custom book booking confirmation email.
    
    Args:
        user_email: User's email address
        user_name: User's full name
        booking_id: Booking identifier
        booking_details: Booking details dictionary
    """
    try:
        logger.info(f'Sending booking confirmation to {user_email} for booking {booking_id}')
        
        from apps.api.app.services.email_service import EmailService
        
        email_service = EmailService()
        result = email_service.send_booking_confirmation(
            to_email=user_email,
            template_data={
                'name': user_name,
                'bookingId': booking_id,
                'title': booking_details.get('title', 'Custom Book'),
                'genre': booking_details.get('genre', 'Not specified'),
                'wordCount': booking_details.get('word_count', 'TBD'),
                'budget': f"${booking_details.get('budget', 0):.2f}",
                'deadline': booking_details.get('deadline', 'To be confirmed'),
                'requirements': booking_details.get('requirements', ''),
                'bookingUrl': f'https://abdulboy-ebook.com/booking-status.html?id={booking_id}',
                'dashboardUrl': 'https://abdulboy-ebook.com/user-dashboard.html',
            }
        )
        
        if result:
            logger.info(f'Booking confirmation sent for booking {booking_id}')
            return {'status': 'success', 'booking_id': booking_id}
        else:
            raise Exception('Failed to send email')
            
    except Exception as e:
        logger.error(f'Failed to send booking confirmation for booking {booking_id}: {e}')
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(name='email_jobs.send_weekly_newsletter', bind=True)
def send_weekly_newsletter(self):
    """
    Send weekly newsletter to all subscribed users.
    Scheduled to run every Monday at 9 AM.
    """
    try:
        logger.info('Starting weekly newsletter job')
        
        from apps.api.app.services.email_service import EmailService
        from apps.api.app.services.user_service import UserService
        
        user_service = UserService()
        email_service = EmailService()
        
        # Get all subscribed users
        users = user_service.get_newsletter_subscribers()
        logger.info(f'Found {len(users)} newsletter subscribers')
        
        # Get new books for the week
        from apps.api.app.services.book_service import BookService
        book_service = BookService()
        new_books = book_service.get_new_books(days=7, limit=10)
        
        # Get popular books
        popular_books = book_service.get_popular_books(limit=5)
        
        success_count = 0
        for user in users:
            try:
                result = email_service.send_newsletter(
                    to_email=user.email,
                    template_data={
                        'name': user.full_name,
                        'new_books': new_books,
                        'popular_books': popular_books,
                        'unsubscribe_url': f'https://abdulboy-ebook.com/unsubscribe?email={user.email}',
                    }
                )
                if result:
                    success_count += 1
            except Exception as e:
                logger.error(f'Failed to send newsletter to {user.email}: {e}')
        
        logger.info(f'Weekly newsletter sent to {success_count}/{len(users)} users')
        return {'status': 'success', 'sent': success_count, 'total': len(users)}
        
    except Exception as e:
        logger.error(f'Weekly newsletter job failed: {e}')
        raise


@shared_task(name='email_jobs.send_payment_failure_email', bind=True, max_retries=3)
def send_payment_failure_email(
    self,
    user_email: str,
    user_name: str,
    amount: float,
    error_message: str
):
    """
    Send payment failure notification email.
    
    Args:
        user_email: User's email address
        user_name: User's full name
        amount: Failed payment amount
        error_message: Error message from payment gateway
    """
    try:
        logger.info(f'Sending payment failure email to {user_email}')
        
        from apps.api.app.services.email_service import EmailService
        
        email_service = EmailService()
        result = email_service.send_payment_failure_email(
            to_email=user_email,
            template_data={
                'name': user_name,
                'amount': f'${amount:.2f}',
                'error_message': error_message,
                'retry_url': 'https://abdulboy-ebook.com/payment-retry',
                'support_url': 'https://abdulboy-ebook.com/contact',
            }
        )
        
        if result:
            logger.info(f'Payment failure email sent to {user_email}')
            return {'status': 'success', 'user_email': user_email}
        else:
            raise Exception('Failed to send email')
            
    except Exception as e:
        logger.error(f'Failed to send payment failure email to {user_email}: {e}')
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(name='email_jobs.send_subscription_expiring_email')
def send_subscription_expiring_email(user_email: str, user_name: str, days_left: int):
    """
    Send subscription expiring soon notification.
    
    Args:
        user_email: User's email address
        user_name: User's full name
        days_left: Number of days until expiration
    """
    try:
        logger.info(f'Sending subscription expiring email to {user_email}, {days_left} days left')
        
        from apps.api.app.services.email_service import EmailService
        
        email_service = EmailService()
        result = email_service.send_subscription_expiring_email(
            to_email=user_email,
            template_data={
                'name': user_name,
                'days_left': days_left,
                'renew_url': 'https://abdulboy-ebook.com/subscription-plans.html',
            }
        )
        
        return {'status': 'success' if result else 'failed', 'user_email': user_email}
        
    except Exception as e:
        logger.error(f'Failed to send subscription expiring email to {user_email}: {e}')
        return {'status': 'error', 'error': str(e)}
