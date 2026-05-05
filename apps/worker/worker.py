#!/usr/bin/env python
"""
Celery Worker Entry Point
=========================
Starts the Celery worker for background task processing.
"""

import os
import sys
import signal
import logging
from celery import current_app
from celery.bin import worker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/worker/worker.log')
    ]
)
logger = logging.getLogger(__name__)

# Set environment
os.environ.setdefault('APP_ENV', 'development')


def signal_handler(signum, frame):
    """Handle termination signals gracefully."""
    logger.info(f'Received signal {signum}, shutting down worker...')
    current_app.control.shutdown()
    sys.exit(0)


def main():
    """Main entry point for the worker."""
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Get command line arguments
    argv = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # Default arguments if none provided
    if not argv:
        argv = [
            '-A', 'celery_app',
            '--loglevel=info',
            '--concurrency=4',
            '--queues=email,pdf_processing,backup,export,cleanup,notifications,default',
            '--hostname=worker-%h',
            '--max-tasks-per-child=1000',
            '--time-limit=1800',
            '--soft-time-limit=1500',
        ]
    
    logger.info(f'Starting Celery worker with args: {argv}')
    
    # Start the worker
    worker_app = worker.worker(app=current_app)
    
    try:
        worker_app.run(argv)
    except KeyboardInterrupt:
        logger.info('Worker stopped by user')
    except Exception as e:
        logger.error(f'Worker failed: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
