"""
Constants Module
================
Application-wide constants and enumerations.
"""

# =============================================================================
# User Constants
# =============================================================================
USER_ROLES = {
    "ADMIN": "admin",
    "SPECIAL": "special",
    "NORMAL": "normal",
}

USER_ROLES_LIST = list(USER_ROLES.values())

SUBSCRIPTION_STATUSES = {
    "FREE": "free",
    "BASIC": "basic",
    "PREMIUM": "premium",
    "CANCELLED": "cancelled",
    "EXPIRED": "expired",
}

# =============================================================================
# Book Constants
# =============================================================================
BOOK_STATUSES = {
    "DRAFT": "draft",
    "PUBLISHED": "published",
    "ARCHIVED": "archived",
}

BOOK_STATUSES_LIST = list(BOOK_STATUSES.values())

BOOK_LANGUAGES = [
    "en",  # English
    "fr",  # French
    "es",  # Spanish
    "de",  # German
    "zh",  # Chinese
    "ja",  # Japanese
    "ar",  # Arabic
    "hi",  # Hindi
    "sw",  # Swahili
    "ha",  # Hausa
    "yo",  # Yoruba
    "ig",  # Igbo
]

MAX_PREVIEW_PAGES = 50
DEFAULT_PREVIEW_PAGES = 10

# =============================================================================
# Payment Constants
# =============================================================================
PAYMENT_STATUSES = {
    "PENDING": "pending",
    "COMPLETED": "completed",
    "FAILED": "failed",
    "REFUNDED": "refunded",
    "CANCELLED": "cancelled",
}

PAYMENT_METHODS = {
    "STRIPE": "stripe",
    "OPAY": "opay",
    "PAYPAL": "paypal",
    "FLUTTERWAVE": "flutterwave",
}

PAYMENT_ITEM_TYPES = {
    "BOOK": "book",
    "SUBSCRIPTION": "subscription",
    "CUSTOM_BOOKING": "custom_booking",
}

CURRENCIES = {
    "USD": {
        "symbol": "$",
        "decimal_places": 2,
    },
    "NGN": {
        "symbol": "₦",
        "decimal_places": 2,
    },
    "EUR": {
        "symbol": "€",
        "decimal_places": 2,
    },
    "GBP": {
        "symbol": "£",
        "decimal_places": 2,
    },
}

# =============================================================================
# Subscription Constants
# =============================================================================
SUBSCRIPTION_PLANS = {
    "FREE": {
        "id": "free",
        "name": "Free",
        "books_per_month": 3,
        "download_limit": 3,
        "price": 0,
    },
    "BASIC": {
        "id": "basic",
        "name": "Basic",
        "books_per_month": 10,
        "download_limit": 5,
        "price": 9.99,
    },
    "PREMIUM": {
        "id": "premium",
        "name": "Premium",
        "books_per_month": None,  # Unlimited
        "download_limit": None,   # Unlimited
        "price": 19.99,
    },
}

# =============================================================================
# Booking Constants
# =============================================================================
BOOKING_STATUSES = {
    "PENDING": "pending",
    "ACCEPTED": "accepted",
    "IN_PROGRESS": "in_progress",
    "COMPLETED": "completed",
    "CANCELLED": "cancelled",
    "DELIVERED": "delivered",
}

BOOKING_GENRES = [
    "Fiction",
    "Non-Fiction",
    "Mystery",
    "Thriller",
    "Romance",
    "Science Fiction",
    "Fantasy",
    "Horror",
    "Biography",
    "Self-Help",
    "Business",
    "Technology",
    "Education",
    "Children",
    "Poetry",
]

# =============================================================================
# Gamification Constants
# =============================================================================
BADGE_RARITIES = {
    "COMMON": "common",
    "RARE": "rare",
    "EPIC": "epic",
    "LEGENDARY": "legendary",
}

BADGE_CRITERIA_TYPES = {
    "BOOKS_READ": "books_read",
    "REVIEWS_WRITTEN": "reviews_written",
    "PURCHASE_COUNT": "purchase_count",
    "STREAK_DAYS": "streak_days",
    "TOTAL_POINTS": "total_points",
}

# =============================================================================
# Cache Constants
# =============================================================================
CACHE_TTL = {
    "BOOK_LIST": 300,      # 5 minutes
    "BOOK_DETAIL": 600,    # 10 minutes
    "USER_PROFILE": 1800,  # 30 minutes
    "CATEGORIES": 86400,   # 24 hours
    "SETTINGS": 3600,      # 1 hour
}

# =============================================================================
# Rate Limit Constants
# =============================================================================
RATE_LIMITS = {
    "DEFAULT": {"requests": 100, "period": 60},
    "AUTH": {"requests": 10, "period": 60},
    "PAYMENT": {"requests": 20, "period": 60},
    "UPLOAD": {"requests": 50, "period": 3600},
    "API_KEY": {"requests": 1000, "period": 60},
}

# =============================================================================
# File Upload Constants
# =============================================================================
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
ALLOWED_DOCUMENT_TYPES = ["application/pdf", "application/epub+zip", "application/x-mobipocket-ebook"]
ALLOWED_AVATAR_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
