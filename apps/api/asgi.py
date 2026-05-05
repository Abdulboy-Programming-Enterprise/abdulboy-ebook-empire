"""
ASGI Configuration
==================
Async Server Gateway Interface configuration for the FastAPI application.
"""

import os
from app.app import create_app

# Create ASGI application
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "asgi:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
