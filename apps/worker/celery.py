"""
Celery Application Configuration
================================
Background task queue configuration for Abdulboy Ebook Empire.
Handles async tasks: email sending, PDF processing, backups, data exports, etc.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module (if using Django, otherwise ignore)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.config.settings')

# Create Celery application
app = Celery('abdulboy_ebook_empire')

# Load configuration from environment or config file
app.config_from_object('celery_config', namespace='CELERY')

# Auto-discover tasks from all registered modules
app.autodiscover_tasks(['apps.worker.jobs'])

# =============================================================================
# Celery Configuration
# =============================================================================
CELERY_CONFIG = {
    # Broker settings (Redis)
    'broker_url': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    'result_backend': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    
    # Task serialization
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json'],
    'timezone': 'Africa/Lagos',
    'enable_utc': True,
    
    # Task execution
    'task_track_started': True,
    'task_time_limit': 30 * 60,  # 30 minutes
    'task_soft_time_limit': 25 * 60,  # 25 minutes
    
    # Task results
    'result_expires': 60 * 60 * 24,  # 1 day
    
    # Worker settings
    'worker_prefetch_multiplier': 4,
    'worker_max_tasks_per_child': 1000,
    'worker_max_memory_per_child': 200 * 1024 * 1024,  # 200MB
    
    # Task routes
    'task_routes': {
        'apps.worker.jobs.email_jobs.*': {'queue': 'email'},
        'apps.worker.jobs.pdf_jobs.*': {'queue': 'pdf_processing'},
        'apps.worker.jobs.backup_jobs.*': {'queue': 'backup'},
        'apps.worker.jobs.export_jobs.*': {'queue': 'export'},
        'apps.worker.jobs.cleanup_jobs.*': {'queue': 'cleanup'},
        'apps.worker.jobs.notification_jobs.*': {'queue': 'notifications'},
    },
    
    # Task queues
    'task_queues': {
        'email': {'exchange': 'email', 'routing_key': 'email'},
        'pdf_processing': {'exchange': 'pdf', 'routing_key': 'pdf'},
        'backup': {'exchange': 'backup', 'routing_key': 'backup'},
        'export': {'exchange': 'export', 'routing_key': 'export'},
        'cleanup': {'exchange': 'cleanup', 'routing_key': 'cleanup'},
        'notifications': {'exchange': 'notifications', 'routing_key': 'notifications'},
        'default': {'exchange': 'default', 'routing_key': 'default'},
    },
    
    # Task default rate limit
    'task_default_rate_limit': '100/m',
    
    # Task acks
    'task_acks_late': True,
    'task_reject_on_worker_lost': True,
    
    # Beat schedule
    'beat_schedule': {
        # Daily backup at 2 AM
        'daily-database-backup': {
            'task': 'apps.worker.jobs.backup_jobs.database_backup',
            'schedule': crontab(hour=2, minute=0),
            'options': {'queue': 'backup', 'expires': 3600},
        },
        # Hourly cleanup of temp files
        'hourly-temp-cleanup': {
            'task': 'apps.worker.jobs.cleanup_jobs.cleanup_temp_files',
            'schedule': crontab(minute=0),
            'options': {'queue': 'cleanup', 'expires': 300},
        },
        # Daily cleanup of expired sessions
        'daily-session-cleanup': {
            'task': 'apps.worker.jobs.cleanup_jobs.cleanup_expired_sessions',
            'schedule': crontab(hour=3, minute=0),
            'options': {'queue': 'cleanup', 'expires': 600},
        },
        # Send daily analytics report at 8 AM
        'daily-analytics-report': {
            'task': 'apps.worker.jobs.report_jobs.send_daily_report',
            'schedule': crontab(hour=8, minute=0),
            'options': {'queue': 'email', 'expires': 1800},
        },
        # Weekly newsletter on Monday at 9 AM
        'weekly-newsletter': {
            'task': 'apps.worker.jobs.email_jobs.send_weekly_newsletter',
            'schedule': crontab(day_of_week=1, hour=9, minute=0),
            'options': {'queue': 'email', 'expires': 7200},
        },
        # Update AI recommendation models daily at 4 AM
        'update-recommendations': {
            'task': 'apps.worker.jobs.ml_jobs.update_recommendation_model',
            'schedule': crontab(hour=4, minute=0),
            'options': {'queue': 'ml_processing', 'expires': 3600},
        },
        # Sync analytics data every 15 minutes
        'sync-analytics': {
            'task': 'apps.worker.jobs.analytics_jobs.sync_analytics_data',
            'schedule': crontab(minute='*/15'),
            'options': {'queue': 'analytics', 'expires': 600},
        },
        # Check expiring subscriptions daily at 10 AM
        'check-expiring-subscriptions': {
            'task': 'apps.worker.jobs.subscription_jobs.check_expiring_subscriptions',
            'schedule': crontab(hour=10, minute=0),
            'options': {'queue': 'notifications', 'expires': 1800},
        },
        # Clean up old analytics data weekly on Sunday
        'cleanup-old-analytics': {
            'task': 'apps.worker.jobs.cleanup_jobs.cleanup_old_analytics',
            'schedule': crontab(day_of_week=0, hour=1, minute=0),
            'options': {'queue': 'cleanup', 'expires': 3600},
        },
        # Generate leaderboard daily at midnight
        'generate-leaderboard': {
            'task': 'apps.worker.jobs.gamification_jobs.generate_leaderboard',
            'schedule': crontab(hour=0, minute=0),
            'options': {'queue': 'gamification', 'expires': 1200},
        },
    },
}

# Apply configuration
app.conf.update(**CELERY_CONFIG)


# =============================================================================
# Task Error Handlers
# =============================================================================
@app.task(bind=True, max_retries=3)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')


@app.task(bind=True)
def error_handler(self, *args, **kwargs):
    """Global error handler for failed tasks."""
    print(f'Task {self.request.id} failed: {self.request.retries} retries')
    # Here you would log to Sentry, send alert, etc.


# =============================================================================
# Task Callbacks
# =============================================================================
def on_task_failure(self, exc, task_id, args, kwargs, einfo):
    """Callback when a task fails."""
    print(f'Task {task_id} failed: {exc}')
    # Send alert to monitoring system
    # Could send to Slack, Sentry, etc.


def on_task_success(self, retval, task_id, args, kwargs):
    """Callback when a task succeeds."""
    print(f'Task {task_id} completed successfully')


# =============================================================================
# Worker Health Check
# =============================================================================
@app.task(name='health_check')
def health_check():
    """Health check endpoint for the worker."""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_tasks': app.control.inspect().active() or {},
    }


if __name__ == '__main__':
    app.start()
