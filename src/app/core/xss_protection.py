"""
XSS Protection utilities - Security Hardened v8.4.3
ANO TsPS INN 9724016805
"""

import re
import html
from typing import Optional


def sanitize_html(text: str) -> str:
    """
    Sanitize text for safe HTML output.
    Escapes all HTML entities to prevent XSS.
    """
    if not text:
        return ""

    # First escape HTML entities
    sanitized = html.escape(text)

    return sanitized


def sanitize_for_text_content(text: str) -> str:
    """
    Sanitize for textContent (no HTML allowed at all)
    """
    if not text:
        return ""

    # Remove all HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Escape remaining content
    text = html.escape(text)

    return text


def sanitize_markdown(text: str) -> str:
    """
    Sanitize markdown input - allow only safe markdown
    """
    if not text:
        return ""

    # Remove script tags and event handlers
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)

    return text


# Frontend-safe message formatter
def format_safe_message(message: str) -> str:
    """Format message for safe DOM insertion using textContent"""
    return sanitize_for_text_content(message)
