"""Unit tests for scope validation and output validation.

Acceptance criteria:
- Zero drug/dosage/surgery/ingestible Ayurvedic product recommendations
- Every factual claim has valid provenance
"""

from __future__ import annotations

import pytest

from medicobuddy.safety.output_validator import validate_output, check_provenance
from medicobuddy.safety.scope_validator import validate_query_scope


class TestScopeValidator:
    """Test query scope validation."""

    def test_blocks_medication_request(self) -> None:
        result = validate_query_scope("Can you prescribe me some medicine for my headache?")
        assert not result.in_scope

    def test_blocks_drug_name_request(self) -> None:
        result = validate_query_scope("Should I take paracetamol or ibuprofen?")
        assert not result.in_scope

    def test_blocks_dosage_request(self) -> None:
        result = validate_query_scope("What dose of aspirin should I take?")
        assert not result.in_scope

    def test_blocks_surgery_request(self) -> None:
        result = validate_query_scope("Do I need surgery for my stomach pain?")
        assert not result.in_scope

    def test_blocks_ayurvedic_formulation_request(self) -> None:
        result = validate_query_scope("What bhasma should I take for my fever?")
        assert not result.in_scope

    def test_blocks_churna_request(self) -> None:
        result = validate_query_scope("Can I take triphala churna for digestion?")
        assert not result.in_scope

    def test_blocks_panchakarma_request(self) -> None:
        result = validate_query_scope("Should I do panchakarma for detox?")
        assert not result.in_scope

    def test_blocks_diagnosis_request(self) -> None:
        result = validate_query_scope("What disease do I have?")
        assert not result.in_scope

    def test_allows_symptom_query(self) -> None:
        result = validate_query_scope("I have a mild headache, what can I do at home?")
        assert result.in_scope

    def test_allows_nausea_query(self) -> None:
        result = validate_query_scope("I feel nauseous, any tips?")
        assert result.in_scope


class TestOutputValidator:
    """Test output safety scanning."""

    def test_blocks_drug_names_in_output(self) -> None:
        result = validate_output("You should take paracetamol 500mg twice a day")
        assert not result.is_safe
        assert any(v.category == "DRUG" for v in result.violations)

    def test_blocks_ayurveda_ingestible(self) -> None:
        result = validate_output("Take ashwagandha tablet 500mg before bed")
        assert not result.is_safe

    def test_blocks_surgery_mention(self) -> None:
        result = validate_output("You may need surgery for this condition")
        assert not result.is_safe

    def test_blocks_diagnosis_language(self) -> None:
        result = validate_output("You have a bacterial infection")
        assert not result.is_safe

    def test_blocks_cure_guarantee(self) -> None:
        result = validate_output("This will cure your headache completely")
        assert not result.is_safe

    def test_blocks_no_doctor_needed(self) -> None:
        result = validate_output("There is no need to see a doctor for this")
        assert not result.is_safe

    def test_allows_safe_response(self) -> None:
        result = validate_output(
            "Resting in a quiet, dark room may help ease mild headache discomfort. "
            "Staying hydrated with plain water is generally recommended. "
            "If symptoms worsen, please consult a healthcare professional."
        )
        assert result.is_safe

    def test_allows_hedged_language(self) -> None:
        result = validate_output(
            "Some evidence suggests that adequate sleep may help with fatigue. "
            "Evidence is limited for this approach."
        )
        assert result.is_safe


class TestProvenanceCheck:
    """Test citation provenance validation."""

    def test_warns_on_claims_without_citations(self) -> None:
        warnings = check_provenance(
            "Studies show that rest helps with headaches",
            citation_urls=[],
        )
        assert len(warnings) > 0

    def test_warns_on_citation_mismatch(self) -> None:
        warnings = check_provenance(
            "According to research [1] and data [2] and more [3]",
            citation_urls=["https://example.com/1"],
        )
        assert len(warnings) > 0

    def test_no_warning_for_supported_claims(self) -> None:
        warnings = check_provenance(
            "Rest in a quiet room may provide comfort.",
            citation_urls=[],
        )
        assert len(warnings) == 0
