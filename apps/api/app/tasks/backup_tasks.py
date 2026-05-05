"""
Backup Tasks
============
Celery tasks for database and file backups.
"""

from celery import shared_task
from datetime import datetime
import subprocess
import os
import boto3
from app.core.config import settings
from app.core.logger import logger


@shared_task(name="database_backup")
def database_backup():
    """
    Create a database backup using pg_dump.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.sql.gz"
        backup_path = f"/storage/backups/{backup_filename}"
        
        # Create backup directory if not exists
        os.makedirs("/storage/backups", exist_ok=True)
        
        # Run pg_dump
        cmd = f"pg_dump {settings.DATABASE_URL} | gzip > {backup_path}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"pg_dump failed: {result.stderr}")
        
        file_size = os.path.getsize(backup_path)
        logger.info(f"Database backup created: {backup_filename} ({file_size / 1024 / 1024:.2f} MB)")
        
        # Upload to S3 if configured
        if settings.AWS_ACCESS_KEY_ID:
            upload_backup_to_s3.delay(backup_path, backup_filename)
        
        # Cleanup old backups (keep last 30)
        cleanup_old_backups.delay()
        
        return {
            "status": "success",
            "filename": backup_filename,
            "size_mb": file_size / 1024 / 1024
        }
        
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="upload_backup_to_s3")
def upload_backup_to_s3(backup_path: str, filename: str):
    """
    Upload backup file to S3.
    """
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        
        bucket = settings.AWS_BUCKET_NAME
        key = f"backups/database/{filename}"
        
        s3_client.upload_file(backup_path, bucket, key)
        logger.info(f"Backup uploaded to S3: {key}")
        
        return {"status": "success", "s3_key": key}
        
    except Exception as e:
        logger.error(f"Failed to upload backup to S3: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="cleanup_old_backups")
def cleanup_old_backups():
    """
    Delete backup files older than 30 days.
    """
    try:
        backup_dir = "/storage/backups"
        if not os.path.exists(backup_dir):
            return {"status": "skipped"}
        
        cutoff = datetime.now().timestamp() - (30 * 24 * 60 * 60)
        deleted_count = 0
        deleted_size = 0
        
        for filename in os.listdir(backup_dir):
            filepath = os.path.join(backup_dir, filename)
            if os.path.isfile(filepath):
                mtime = os.path.getmtime(filepath)
                if mtime < cutoff:
                    size = os.path.getsize(filepath)
                    os.remove(filepath)
                    deleted_count += 1
                    deleted_size += size
        
        logger.info(f"Cleaned up {deleted_count} old backups, freed {deleted_size / 1024 / 1024:.2f} MB")
        return {"status": "success", "deleted_count": deleted_count, "freed_mb": deleted_size / 1024 / 1024}
        
    except Exception as e:
        logger.error(f"Failed to cleanup old backups: {e}")
        return {"status": "error", "error": str(e)}
