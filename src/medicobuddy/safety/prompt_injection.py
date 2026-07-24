"""Prompt injection detection and input sanitization.

Protects against:
1. Direct prompt injection in user messages
2. Indirect injection in retrieved documents (treated as untrusted data)
3. System prompt extraction attempts
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class InjectionCheckResult:
    """Result of prompt injection detection."""

    is_safe: bool
    detected_patterns: list[str]
    sanitized_text: str
    risk_level: str  # "none", "low", "medium", "high"


# ── Injection patterns (user input) ──────────────────────────
USER_INJECTION_PATTERNS: list[tuple[str, str]] = [
    (r"ignore\s+(?:all\s+)?(?:previous|above|prior|earlier)\s+(?:instructions?|rules?|prompts?)", "high"),
    (r"forget\s+(?:all\s+)?(?:your|the)\s+(?:instructions?|rules?|guidelines?|constraints?)", "high"),
    (r"you\s+are\s+now\s+(?:a|an)\s+(?:different|new|unrestricted)", "high"),
    (r"act\s+as\s+(?:a|an)\s+(?:doctor|physician|medical\s+professional)", "high"),
    (r"prescribe\s+(?:me|us)\s+(?:a\s+)?(?:medicine|drug|medication)", "medium"),
    (r"bypass\s+(?:safety|security|filter|restriction|rule)", "high"),
    (r"override\s+(?:safety|security|filter|restriction|rule)", "high"),
    (r"disable\s+(?:safety|security|filter|restriction|rule)", "high"),
    (r"(?:system|developer)\s+(?:prompt|message|instruction)", "medium"),
    (r"what\s+(?:are|is)\s+your\s+(?:system\s+)?(?:prompt|instructions?|rules?)", "medium"),
    (r"repeat\s+(?:your|the)\s+(?:system|initial)\s+(?:prompt|message|instructions?)", "medium"),
    (r"jailbreak", "high"),
    (r"dan\s+mode", "high"),
    (r"do\s+anything\s+now", "high"),
    (r"(?:roleplay|pretend)\s+(?:as|you'?re)\s+(?:a\s+)?(?:doctor|physician|expert)", "medium"),
]

# ── Injection patterns in retrieved documents ────────────────
DOCUMENT_INJECTION_PATTERNS: list[tuple[str, str]] = [
    (r"<\s*(?:system|assistant|instruction|prompt)\s*>", "high"),
    (r"\[(?:system|instruction|prompt)\]", "high"),
    (r"(?:IMPORTANT|URGENT|OVERRIDE):\s*(?:ignore|forget|disregard)", "high"),
    (r"(?:new\s+)?instructions?:\s*(?:you\s+(?:must|should|will))", "high"),
    (r"(?:admin|root|sudo)\s*:\s*", "medium"),
]

_COMPILED_USER: list[tuple[re.Pattern[str], str]] = [
    (re.compile(p, re.IGNORECASE), level) for p, level in USER_INJECTION_PATTERNS
]

_COMPILED_DOC: list[tuple[re.Pattern[str], str]] = [
    (re.compile(p, re.IGNORECASE), level) for p, level in DOCUMENT_INJECTION_PATTERNS
]


def check_user_input(text: str) -> InjectionCheckResult:
    """Check user input for prompt injection attempts.

    Args:
        text: Raw user input text.

    Returns:
        InjectionCheckResult with safety status and detected patterns.
    """
    detected: list[str] = []
    max_risk = "none"
    risk_order = {"none": 0, "low": 1, "medium": 2, "high": 3}

    for pattern, level in _COMPILED_USER:
        if pattern.search(text):
            detected.append(pattern.pattern)
            if risk_order.get(level, 0) > risk_order.get(max_risk, 0):
                max_risk = level

    return InjectionCheckResult(
        is_safe=len(detected) == 0,
        detected_patterns=detected,
        sanitized_text=text if not detected else _sanitize_text(text),
        risk_level=max_risk,
    )


def check_retrieved_document(text: str) -> InjectionCheckResult:
    """Check a retrieved document for embedded injection attempts.

    Retrieved text is ALWAYS treated as untrusted data, never as instructions.

    Args:
        text: Retrieved document text.

    Returns:
        InjectionCheckResult with safety status and detected patterns.
    """
    detected: list[str] = []
    max_risk = "none"
    risk_order = {"none": 0, "low": 1, "medium": 2, "high": 3}

    for pattern, level in _COMPILED_DOC:
        if pattern.search(text):
            detected.append(pattern.pattern)
            if risk_order.get(level, 0) > risk_order.get(max_risk, 0):
                max_risk = level

    # Also check user-facing injection patterns in documents
    for pattern, level in _COMPILED_USER:
        if pattern.search(text):
            detected.append(f"[doc]{pattern.pattern}")
            if risk_order.get(level, 0) > risk_order.get(max_risk, 0):
                max_risk = level

    sanitized = _sanitize_document(text) if detected else text

    return InjectionCheckResult(
        is_safe=len(detected) == 0,
        detected_patterns=detected,
        sanitized_text=sanitized,
        risk_level=max_risk,
    )


def _sanitize_text(text: str) -> str:
    """Remove or neutralize injection patterns from user input."""
    sanitized = text
    for pattern, _ in _COMPILED_USER:
        sanitized = pattern.sub("[FILTERED]", sanitized)
    return sanitized


def _sanitize_document(text: str) -> str:
    """Remove injection patterns from retrieved documents."""
    sanitized = text
    for pattern, _ in _COMPILED_DOC:
        sanitized = pattern.sub("", sanitized)
    for pattern, _ in _COMPILED_USER:
        sanitized = pattern.sub("", sanitized)
    return sanitized.strip()
