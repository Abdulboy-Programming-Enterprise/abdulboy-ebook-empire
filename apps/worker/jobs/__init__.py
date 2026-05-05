"""
Celery Jobs Package
===================
Contains all background task definitions for the Abdulboy Ebook Empire.
"""

from apps.worker.jobs import (
    email_jobs,
    cleanup_jobs,
    backup_jobs,
    report_jobs,
    ml_jobs,
    analytics_jobs,
    subscription_jobs,
    gamification_jobs,
    pdf_jobs,
    notification_jobs,
)

__all__ = [
    'email_jobs',
    'cleanup_jobs',
    'backup_jobs',
    'report_jobs',
    'ml_jobs',
    'analytics_jobs',
    'subscription_jobs',
    'gamification_jobs',
    'pdf_jobs',
    'notification_jobs',
]
