"""
Validators Module
=================
Input validation functions for various data types.
"""

import re
from typing import Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email:
        return False, "Email is required"
    if not re.match(pattern, email):
        return False, "Invalid email format"
    return True, ""


def validate_phone(phone: str) -> Tuple[bool, str]:
    """Validate phone number format (international)."""
    # Basic international phone validation
    pattern = r'^\+?[1-9]\d{1,14}$'
    if not phone:
        return True, ""  # Phone is optional
    if not re.match(pattern, phone):
        return False, "Invalid phone number format"
    return True, ""


def validate_password_strength(password: str) -> Tuple[bool, str, int]:
    """
    Validate password strength.
    Returns (is_valid, message, strength_score).
    Strength score: 0-4 (weak to very strong)
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters", 0
    
    score = 0
    if re.search(r'[a-z]', password):
        score += 1
    if re.search(r'[A-Z]', password):
        score += 1
    if re.search(r'[0-9]', password):
        score += 1
    if re.search(r'[^a-zA-Z0-9]', password):
        score += 1
    
    if score < 2:
        return False, "Password is too weak. Use uppercase, lowercase, numbers, or special characters.", score
    elif score == 2:
        return True, "Password is fair", score
    elif score == 3:
        return True, "Password is good", score
    else:
        return True, "Password is strong", score


def validate_isbn(isbn: str) -> Tuple[bool, str]:
    """Validate ISBN-10 or ISBN-13 format."""
    if not isbn:
        return True, ""  # ISBN is optional
    
    # Remove hyphens and spaces
    isbn = re.sub(r'[\s-]', '', isbn)
    
    # Check ISBN-10
    if len(isbn) == 10:
        if re.match(r'^\d{9}[\dX]$', isbn):
            # Calculate checksum
            total = sum((i + 1) * int(ch) for i, ch in enumerate(isbn[:9]))
            check = total % 11
            check_digit = 'X' if check == 10 else str(check)
            if isbn[9].upper() == check_digit:
                return True, ""
        return False, "Invalid ISBN-10 format"
    
    # Check ISBN-13
    if len(isbn) == 13:
        if re.match(r'^\d{13}$', isbn):
            # Calculate checksum
            total = sum((1 if i % 2 == 0 else 3) * int(ch) for i, ch in enumerate(isbn[:12]))
            check = (10 - (total % 10)) % 10
            if int(isbn[12]) == check:
                return True, ""
        return False, "Invalid ISBN-13 format"
    
    return False, "ISBN must be 10 or 13 digits"


def validate_url(url: str) -> Tuple[bool, str]:
    """Validate URL format."""
    if not url:
        return True, ""
    pattern = r'^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$'
    if re.match(pattern, url):
        return True, ""
    return False, "Invalid URL format"
