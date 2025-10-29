"""
formatters.py — Utility functions for consistent formatting across the app.
"""

from datetime import datetime
from typing import Optional


# -------------------------------
# Date & Time Formatting
# -------------------------------
def format_datetime(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a datetime object into a string. Returns empty string if None.
    """
    if dt is None:
        return ""
    return dt.strftime(fmt)


def format_date(dt: Optional[datetime], fmt: str = "%Y-%m-%d") -> str:
    """
    Format a datetime object into a date string. Returns empty string if None.
    """
    if dt is None:
        return ""
    return dt.strftime(fmt)


# -------------------------------
# Number & Currency Formatting
# -------------------------------
def format_number(num: Optional[float], decimals: int = 2) -> str:
    """
    Format a number with fixed decimal places.
    """
    if num is None:
        return "0"
    return f"{num:.{decimals}f}"


def format_currency(amount: Optional[float], currency: str = "$", decimals: int = 2) -> str:
    """
    Format a number as currency.
    """
    if amount is None:
        return f"{currency}0.00"
    return f"{currency}{amount:.{decimals}f}"


# -------------------------------
# Text Formatting
# -------------------------------
def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a long string and append suffix if needed.
    """
    if not text:
        return ""
    return text if len(text) <= max_length else text[:max_length].rstrip() + suffix


def capitalize_text(text: str) -> str:
    """
    Capitalize the first letter of each word.
    """
    if not text:
        return ""
    return text.title()


def lowercase_text(text: str) -> str:
    """
    Convert text to lowercase.
    """
    if not text:
        return ""
    return text.lower()


def uppercase_text(text: str) -> str:
    """
    Convert text to uppercase.
    """
    if not text:
        return ""
    return text.upper()
