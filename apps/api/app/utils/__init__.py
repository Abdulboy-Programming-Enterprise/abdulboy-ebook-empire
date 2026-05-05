"""
Utils Package
=============
Utility functions and helpers for the application.
"""

from app.utils.helpers import (
    generate_id,
    generate_slug,
    get_current_timestamp,
    format_currency,
    calculate_discount,
)
from app.utils.validators import (
    validate_email,
    validate_phone,
    validate_password_strength,
    validate_isbn,
)
from app.utils.constants import (
    USER_ROLES,
    BOOK_STATUSES,
    PAYMENT_STATUSES,
    SUBSCRIPTION_PLANS,
)
from app.utils.decorators import (
    rate_limit,
    log_execution_time,
    retry_on_failure,
    cache_result,
)
from app.utils.pdf_processor import (
    extract_pdf_preview,
    count_pdf_pages,
    generate_pdf_thumbnail,
)
from app.utils.compressor import (
    compress_image,
    compress_pdf,
    optimize_upload,
)

__all__ = [
    "generate_id",
    "generate_slug",
    "get_current_timestamp",
    "format_currency",
    "calculate_discount",
    "validate_email",
    "validate_phone",
    "validate_password_strength",
    "validate_isbn",
    "USER_ROLES",
    "BOOK_STATUSES",
    "PAYMENT_STATUSES",
    "SUBSCRIPTION_PLANS",
    "rate_limit",
    "log_execution_time",
    "retry_on_failure",
    "cache_result",
    "extract_pdf_preview",
    "count_pdf_pages",
    "generate_pdf_thumbnail",
    "compress_image",
    "compress_pdf",
    "optimize_upload",
]
