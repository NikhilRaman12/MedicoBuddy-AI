"""Unit tests for PII redaction."""

from __future__ import annotations

import pytest

from medicobuddy.privacy.pii_redactor import is_pii_free, redact_pii


class TestPIIRedaction:
    """Test PII pattern detection and redaction."""

    def test_redacts_email(self) -> None:
        text = "My email is john.doe@example.com, can you help?"
        result = redact_pii(text)
        assert "john.doe@example.com" not in result
        assert "[EMAIL_REDACTED]" in result

    def test_redacts_phone(self) -> None:
        text = "Call me at 555-123-4567"
        result = redact_pii(text)
        assert "555-123-4567" not in result

    def test_redacts_ip(self) -> None:
        text = "Request from 192.168.1.100"
        result = redact_pii(text)
        assert "192.168.1.100" not in result
        assert "[IP_REDACTED]" in result

    def test_no_pii_passes_through(self) -> None:
        text = "I have a mild headache and need help"
        result = redact_pii(text)
        assert result == text

    def test_is_pii_free_detects_email(self) -> None:
        assert not is_pii_free("Contact me at user@mail.com")

    def test_is_pii_free_clean_text(self) -> None:
        assert is_pii_free("Mild headache for two hours")
