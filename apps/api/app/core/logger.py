"""
Logger Module
=============
Structured logging configuration using Loguru.
"""

import sys
import json
from loguru import logger
from app.config import settings


def serialize_record(record):
    """Serialize log record to JSON format."""
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }
    
    # Add extra fields
    if record.get("extra"):
        subset["extra"] = record["extra"]
    
    return json.dumps(subset)


def setup_logging():
    """Configure logging based on environment."""
    logger.remove()  # Remove default handler
    
    if settings.LOG_FORMAT == "json" and settings.is_production:
        logger.add(
            sys.stdout,
            format=serialize_record,
            level=settings.LOG_LEVEL,
            serialize=False,
        )
    else:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.LOG_LEVEL,
            colorize=True,
        )
    
    # Add file logging for errors
    logger.add(
        "logs/error.log",
        rotation="500 MB",
        retention="10 days",
        level="ERROR",
        format="{time} | {level} | {name}:{function}:{line} - {message}",
    )
    
    logger.info(f"Logging configured with level: {settings.LOG_LEVEL}")
