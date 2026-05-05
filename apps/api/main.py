#!/usr/bin/env python
"""
Abdulboy Ebook Empire - Backend API Entry Point
================================================
FastAPI application entry point for the ebook platform.
"""

import uvicorn
from app.app import create_app

# Create FastAPI application instance
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
