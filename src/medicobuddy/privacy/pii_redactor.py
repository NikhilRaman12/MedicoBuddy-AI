"""PII redaction for logs and stored data."""

from __future__ import annotations

import re


# Pre-compiled PII patterns
_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Email addresses
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL_REDACTED]"),
    # Phone numbers (various formats)
    (re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[PHONE_REDACTED]"),
    # Indian Aadhaar
    (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "[ID_REDACTED]"),
    # SSN (US)
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
    # IP addresses
    (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "[IP_REDACTED]"),
    # Names preceded by common titles
    (re.compile(r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"), "[NAME_REDACTED]"),
    # Dates of birth patterns
    (re.compile(r"\b(?:born|dob|date of birth)[:\s]*\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b", re.IGNORECASE), "[DOB_REDACTED]"),
    # Addresses with postal codes
    (re.compile(r"\b\d{6}\b"), "[PINCODE_REDACTED]"),
]


def redact_pii(text: str) -> str:
    """Remove personally identifiable information from text.

    Args:
        text: Input text potentially containing PII.

    Returns:
        Text with PII patterns replaced by redaction markers.
    """
    result = text
    for pattern, replacement in _PII_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def is_pii_free(text: str) -> bool:
    """Check if text appears to be free of PII."""
    for pattern, _ in _PII_PATTERNS:
        if pattern.search(text):
            return False
    return True
