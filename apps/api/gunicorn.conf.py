"""
Gunicorn Configuration
======================
Production-grade WSGI server configuration.
"""

import multiprocessing
import os

# Server socket
bind = f"{os.getenv('API_HOST', '0.0.0.0')}:{os.getenv('API_PORT', '8000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "abdulboy-api"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if enabled)
keyfile = None
certfile = None

# Reload on code changes (development only)
reload = os.getenv("APP_ENV") == "development"

# Preload application
preload_app = True
