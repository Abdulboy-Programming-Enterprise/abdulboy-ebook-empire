"""
Application Factory
===================
Creates and configures the FastAPI application instance.
"""

from app import create_app

# Create global app instance
app = create_app()

def main():
    """Entry point for running the application."""
    import uvicorn
    from app.config import settings
    
    uvicorn.run(
        "app.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.APP_DEBUG,
        workers=settings.WORKERS if not settings.APP_DEBUG else 1,
    )

if __name__ == "__main__":
    main()
