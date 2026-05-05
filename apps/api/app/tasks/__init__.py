"""
Tasks Package
=============
Celery task definitions for background job processing.
"""

from app.tasks.email_tasks import (
    send_welcome_email,
    send_purchase_confirmation,
    send_password_reset_email,
    send_booking_confirmation,
    send_booking_update,
    send_new_book_notification,
    send_weekly_newsletter,
)
from app.tasks.cleanup_tasks import (
    cleanup_expired_sessions,
    cleanup_temp_files,
    cleanup_old_analytics,
    cleanup_unverified_users,
)
from app.tasks.backup_tasks import (
    database_backup,
    upload_backup_to_s3,
    cleanup_old_backups,
)
from app.tasks.suggestion_tasks import (
    update_recommendation_model,
    generate_user_recommendations,
    update_similarity_matrix,
)
from app.tasks.report_tasks import (
    generate_daily_report,
    generate_weekly_report,
    generate_monthly_report,
)

__all__ = [
    "send_welcome_email",
    "send_purchase_confirmation",
    "send_password_reset_email",
    "send_booking_confirmation",
    "send_booking_update",
    "send_new_book_notification",
    "send_weekly_newsletter",
    "cleanup_expired_sessions",
    "cleanup_temp_files",
    "cleanup_old_analytics",
    "cleanup_unverified_users",
    "database_backup",
    "upload_backup_to_s3",
    "cleanup_old_backups",
    "update_recommendation_model",
    "generate_user_recommendations",
    "update_similarity_matrix",
    "generate_daily_report",
    "generate_weekly_report",
    "generate_monthly_report",
]
