"""
Helper Functions
================
Common utility functions used throughout the application.
"""

import uuid
import re
from datetime import datetime
from typing import Optional
from slugify import slugify as python_slugify


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    unique_id = str(uuid.uuid4()).replace("-", "")
    return f"{prefix}{unique_id}" if prefix else unique_id


def generate_slug(text: str, max_length: int = 100) -> str:
    """Generate a URL-friendly slug from text."""
    slug = python_slugify(text, lowercase=True, max_length=max_length, word_boundary=True)
    return slug


def get_current_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.utcnow()


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount as currency string."""
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "NGN": "₦",
    }
    symbol = symbols.get(currency, "$")
    return f"{symbol}{amount:.2f}"


def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate discounted price."""
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount percent must be between 0 and 100")
    return price * (1 - discount_percent / 100)


def mask_email(email: str) -> str:
    """Mask email address for privacy."""
    if not email:
        return ""
    local, domain = email.split("@")
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask phone number for privacy."""
    if not phone or len(phone) < 8:
        return phone
    return phone[:4] + "****" + phone[-3:]


def get_client_ip(request) -> Optional[str]:
    """Extract client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
