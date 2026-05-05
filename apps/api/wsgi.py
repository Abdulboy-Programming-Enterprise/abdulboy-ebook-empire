"""
WSGI Configuration
==================
Web Server Gateway Interface configuration for backward compatibility.
"""

import os
from app.app import create_app

# Create WSGI application
app = create_app()

if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple("0.0.0.0", 8000, app, use_reloader=True, use_debugger=True)
