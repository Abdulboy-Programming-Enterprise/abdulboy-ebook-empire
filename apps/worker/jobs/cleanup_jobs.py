"""
Cleanup Jobs
============
Background tasks for cleaning up temporary files, expired sessions, and old data.
"""

import os
import shutil
import logging
from datetime import datetime, timedelta
from celery import shared_task
from pathlib import Path

logger = logging.getLogger(__name__)


@shared_task(name='cleanup_jobs.cleanup_temp_files')
def cleanup_temp_files():
    """
    Clean up temporary files older than 24 hours.
    Scheduled to run hourly.
    """
    try:
        logger.info('Starting temp files cleanup')
        
        temp_dir = Path('/app/storage/uploads/temp')
        if not temp_dir.exists():
            logger.info('Temp directory does not exist, skipping')
            return {'status': 'skipped', 'reason': 'directory_not_found'}
        
        cutoff_time = datetime.now() - timedelta(hours=24)
        deleted_count = 0
        deleted_size = 0
        
        for item in temp_dir.iterdir():
            if item.is_file():
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                if mtime < cutoff_time:
                    size = item.stat().st_size
                    item.unlink()
                    deleted_count += 1
                    deleted_size += size
            elif item.is_dir():
                # Check if directory is empty or old
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                if mtime < cutoff_time:
                    shutil.rmtree(item)
                    deleted_count += 1
        
        logger.info(f'Cleaned up {deleted_count} files, freed {deleted_size / 1024 / 1024:.2f} MB')
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'freed_mb': round(deleted_size / 1024 / 1024, 2)
        }
        
    except Exception as e:
        logger.error(f'Temp files cleanup failed: {e}')
        return {'status': 'error', 'error': str(e)}


@shared_task(name='cleanup_jobs.cleanup_expired_sessions')
def cleanup_expired_sessions():
    """
    Clean up expired user sessions from database.
    Scheduled to run daily at 3 AM.
    """
    try:
        logger.info('Starting expired sessions cleanup')
        
        from apps.api.app.core.database import get_db
        from sqlalchemy import delete
        from apps.api.app.models.user import UserSession
        
        db = next(get_db())
        cutoff_time = datetime.now() - timedelta(days=7)
        
        result = db.execute(
            delete(UserSession).where(UserSession.expires_at < cutoff_time)
        )
        db.commit()
        
        deleted_count = result.rowcount
        logger.info(f'Cleaned up {deleted_count} expired sessions')
        
        return {'status': 'success', 'deleted_count': deleted_count}
        
    except Exception as e:
        logger.error(f'Expired sessions cleanup failed: {e}')
        return {'status': 'error', 'error': str(e)}


@shared_task(name='cleanup_jobs.cleanup_old_analytics')
def cleanup_old_analytics():
    """
    Clean up analytics data older than 90 days.
    Scheduled to run weekly on Sunday at 1 AM.
    """
    try:
        logger.info('Starting old analytics cleanup')
        
        from apps.api.app.core.database import get_db
        from sqlalchemy import delete
        from apps.api.app.models.analytics import AnalyticsEvent
        
        db = next(get_db())
        cutoff_time = datetime.now() - timedelta(days=90)
        
        # Delete old analytics events
        result = db.execute(
            delete(AnalyticsEvent).where(AnalyticsEvent.created_at < cutoff_time)
        )
        db.commit()
        
        deleted_count = result.rowcount
        logger.info(f'Cleaned up {deleted_count} old analytics events')
        
        return {'status': 'success', 'deleted_count': deleted_count}
        
    except Exception as e:
        logger.error(f'Old analytics cleanup failed: {e}')
        return {'status': 'error', 'error': str(e)}


@shared_task(name='cleanup_jobs.cleanup_unverified_users')
def cleanup_unverified_users():
    """
    Delete unverified users older than 7 days.
    Scheduled to run daily at 4 AM.
    """
    try:
        logger.info('Starting unverified users cleanup')
        
        from apps.api.app.core.database import get_db
        from sqlalchemy import delete
        from apps.api.app.models.user import User
        
        db = next(get_db())
        cutoff_time = datetime.now() - timedelta(days=7)
        
        # Delete unverified users
        result = db.execute(
            delete(User).where(
                User.email_verified_at.is_(None),
                User.created_at < cutoff_time
            )
        )
        db.commit()
        
        deleted_count = result.rowcount
        logger.info(f'Cleaned up {deleted_count} unverified users')
        
        return {'status': 'success', 'deleted_count': deleted_count}
        
    except Exception as e:
        logger.error(f'Unverified users cleanup failed: {e}')
        return {'status': 'error', 'error': str(e)}


@shared_task(name='cleanup_jobs.cleanup_old_backups')
def cleanup_old_backups():
    """
    Delete backup files older than 30 days.
    Scheduled to run daily at 3 AM.
    """
    try:
        logger.info('Starting old backups cleanup')
        
        backup_dir = Path('/storage/backups')
        if not backup_dir.exists():
            logger.info('Backup directory does not exist, skipping')
            return {'status': 'skipped', 'reason': 'directory_not_found'}
        
        cutoff_time = datetime.now() - timedelta(days=30)
        deleted_count = 0
        deleted_size = 0
        
        for item in backup_dir.iterdir():
            if item.is_file():
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                if mtime < cutoff_time:
                    size = item.stat().st_size
                    item.unlink()
                    deleted_count += 1
                    deleted_size += size
        
        logger.info(f'Cleaned up {deleted_count} old backups, freed {deleted_size / 1024 / 1024 / 1024:.2f} GB')
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'freed_gb': round(deleted_size / 1024 / 1024 / 1024, 2)
        }
        
    except Exception as e:
        logger.error(f'Old backups cleanup failed: {e}')
        return {'status': 'error', 'error': str(e)}


@shared_task(name='cleanup_jobs.cleanup_failed_uploads')
def cleanup_failed_uploads():
    """
    Clean up failed uploads and orphaned files.
    Scheduled to run every 6 hours.
    """
    try:
        logger.info('Starting failed uploads cleanup')
        
        uploads_dir = Path('/storage/uploads')
        if not uploads_dir.exists():
            return {'status': 'skipped', 'reason': 'directory_not_found'}
        
        # Look for .tmp files older than 1 hour
        cutoff_time = datetime.now() - timedelta(hours=1)
        deleted_count = 0
        
        for item in uploads_dir.rglob('*.tmp'):
            if item.is_file():
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                if mtime < cutoff_time:
                    item.unlink()
                    deleted_count += 1
        
        logger.info(f'Cleaned up {deleted_count} failed upload files')
        return {'status': 'success', 'deleted_count': deleted_count}
        
    except Exception as e:
        logger.error(f'Failed uploads cleanup failed: {e}')
        return {'status': 'error', 'error': str(e)}


@shared_task(name='cleanup_jobs.cleanup_old_notifications')
def cleanup_old_notifications():
    """
    Delete read notifications older than 30 days.
    Scheduled to run daily at 5 AM.
    """
    try:
        logger.info('Starting old notifications cleanup')
        
        from apps.api.app.core.database import get_db
        from sqlalchemy import delete, and_
        from apps.api.app.models.notification import Notification
        
        db = next(get_db())
        cutoff_time = datetime.now() - timedelta(days=30)
        
        # Delete read notifications older than 30 days
        result = db.execute(
            delete(Notification).where(
                and_(
                    Notification.is_read == True,
                    Notification.created_at < cutoff_time
                )
            )
        )
        db.commit()
        
        deleted_count = result.rowcount
        logger.info(f'Cleaned up {deleted_count} old notifications')
        
        return {'status': 'success', 'deleted_count': deleted_count}
        
    except Exception as e:
        logger.error(f'Old notifications cleanup failed: {e}')
        return {'status': 'error', 'error': str(e)}
