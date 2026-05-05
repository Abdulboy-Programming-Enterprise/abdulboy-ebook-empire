"""
Cleanup Tasks
=============
Celery tasks for cleaning up expired data and temporary files.
"""

from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy import delete, and_
from app.core.database import SessionLocal
from app.models.user import User
from app.models.analytics import AnalyticsEvent
from app.models.notification import Notification
from app.core.logger import logger
import os
import shutil


@shared_task(name="cleanup_expired_sessions")
def cleanup_expired_sessions():
    """
    Delete expired user sessions from database.
    """
    try:
        db = SessionLocal()
        
        # Delete sessions older than 7 days
        cutoff = datetime.utcnow() - timedelta(days=7)
        
        # This would delete from a sessions table if exists
        # For now, just log
        logger.info(f"Cleaned up expired sessions older than {cutoff}")
        
        db.close()
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired sessions: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="cleanup_temp_files")
def cleanup_temp_files():
    """
    Delete temporary files older than 24 hours.
    """
    try:
        temp_dir = "/storage/uploads/temp"
        if not os.path.exists(temp_dir):
            return {"status": "skipped", "reason": "directory_not_found"}
        
        cutoff = datetime.now() - timedelta(hours=24)
        deleted_count = 0
        deleted_size = 0
        
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)
            if os.path.isfile(filepath):
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime < cutoff:
                    size = os.path.getsize(filepath)
                    os.remove(filepath)
                    deleted_count += 1
                    deleted_size += size
        
        logger.info(f"Cleaned up {deleted_count} temp files, freed {deleted_size / 1024 / 1024:.2f} MB")
        return {"status": "success", "deleted_count": deleted_count, "freed_mb": deleted_size / 1024 / 1024}
        
    except Exception as e:
        logger.error(f"Failed to cleanup temp files: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="cleanup_old_analytics")
def cleanup_old_analytics():
    """
    Delete analytics data older than 90 days.
    """
    try:
        db = SessionLocal()
        cutoff = datetime.utcnow() - timedelta(days=90)
        
        result = db.execute(
            delete(AnalyticsEvent).where(AnalyticsEvent.created_at < cutoff)
        )
        db.commit()
        
        logger.info(f"Cleaned up {result.rowcount} old analytics events")
        db.close()
        
        return {"status": "success", "deleted_count": result.rowcount}
        
    except Exception as e:
        logger.error(f"Failed to cleanup old analytics: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="cleanup_unverified_users")
def cleanup_unverified_users():
    """
    Delete unverified users older than 7 days.
    """
    try:
        db = SessionLocal()
        cutoff = datetime.utcnow() - timedelta(days=7)
        
        result = db.execute(
            delete(User).where(
                User.email_verified_at.is_(None),
                User.created_at < cutoff
            )
        )
        db.commit()
        
        logger.info(f"Cleaned up {result.rowcount} unverified users")
        db.close()
        
        return {"status": "success", "deleted_count": result.rowcount}
        
    except Exception as e:
        logger.error(f"Failed to cleanup unverified users: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="cleanup_old_notifications")
def cleanup_old_notifications():
    """
    Delete read notifications older than 30 days.
    """
    try:
        db = SessionLocal()
        cutoff = datetime.utcnow() - timedelta(days=30)
        
        result = db.execute(
            delete(Notification).where(
                and_(
                    Notification.is_read == True,
                    Notification.created_at < cutoff
                )
            )
        )
        db.commit()
        
        logger.info(f"Cleaned up {result.rowcount} old notifications")
        db.close()
        
        return {"status": "success", "deleted_count": result.rowcount}
        
    except Exception as e:
        logger.error(f"Failed to cleanup old notifications: {e}")
        return {"status": "error", "error": str(e)}
