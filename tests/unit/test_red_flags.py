"""Unit tests for the deterministic red-flag triage engine.

Tests ALL required benchmark red-flag scenarios.
Acceptance: 100% of benchmark red-flag cases must trigger escalation.
"""

from __future__ import annotations

import pytest

from medicobuddy.models.symptom import TriageOutcome
from medicobuddy.models.user_context import AgeRange, PregnancyStatus, UserContext
from medicobuddy.safety.red_flags import detect_red_flags, run_triage


# ═══════════════════════════════════════════════════════════
# Benchmark Red-Flag Scenarios (100% escalation required)
# ═══════════════════════════════════════════════════════════

class TestBenchmarkRedFlags:
    """Every benchmark scenario MUST trigger escalation."""

    def test_thunderclap_headache(self) -> None:
        """RF008: Sudden worst-ever headache."""
        result = run_triage("I have the worst headache of my life, it came on suddenly")
        assert result.outcome == TriageOutcome.URGENT_CARE
        assert any(rf.flag_id == "RF008" for rf in result.red_flags_detected)

    def test_fever_with_stiff_neck(self) -> None:
        """RF010 + RF017: Fever with stiff neck — possible meningitis."""
        result = run_triage("I have a fever and my neck is very stiff")
        assert result.outcome == TriageOutcome.URGENT_CARE
        flags = {rf.flag_id for rf in result.red_flags_detected}
        assert "RF010" in flags or "RF017" in flags

    def test_chest_pain_and_nausea(self) -> None:
        """RF001: Chest pain — possible cardiac event."""
        result = run_triage("I am feeling chest pain and nausea")
        assert result.outcome == TriageOutcome.URGENT_CARE
        assert any(rf.flag_id == "RF001" for rf in result.red_flags_detected)

    def test_right_sided_severe_abdominal_pain(self) -> None:
        """RF012: Severe localized abdominal pain — possible appendicitis."""
        result = run_triage("I have severe right lower abdominal pain")
        assert result.outcome == TriageOutcome.URGENT_CARE
        assert any(rf.flag_id == "RF012" for rf in result.red_flags_detected)

    def test_persistent_vomiting_dehydration(self) -> None:
        """RF015: Cannot retain fluids."""
        result = run_triage("I have been vomiting all day and can't keep anything down")
        assert result.outcome == TriageOutcome.URGENT_CARE
        assert any(rf.flag_id == "RF015" for rf in result.red_flags_detected)

    def test_pregnancy_with_abdominal_pain(self) -> None:
        """RF018: Pregnancy with pain."""
        ctx = UserContext(pregnancy_status=PregnancyStatus.PREGNANT)
        result = run_triage("I am pregnant and having abdominal pain and fever", user_context=ctx)
        assert result.outcome in {TriageOutcome.URGENT_CARE, TriageOutcome.OUT_OF_SCOPE}

    def test_infant_user(self) -> None:
        """Out of scope: Under 18."""
        ctx = UserContext(age_range=AgeRange.UNDER_18)
        result = run_triage("My 5-year-old has a headache", user_context=ctx)
        assert result.outcome == TriageOutcome.OUT_OF_SCOPE

    def test_elderly_user(self) -> None:
        """Out of scope: Over 65."""
        ctx = UserContext(age_range=AgeRange.OVER_65)
        result = run_triage("I am 78 and feeling tired", user_context=ctx)
        assert result.outcome == TriageOutcome.OUT_OF_SCOPE

    def test_immunocompromised_with_fever(self) -> None:
        """Out of scope: Immunocompromised."""
        ctx = UserContext(is_immunocompromised=True, age_range=AgeRange.AGE_36_45)
        result = run_triage("I have a mild fever", user_context=ctx)
        assert result.outcome == TriageOutcome.OUT_OF_SCOPE

    def test_blood_in_vomit(self) -> None:
        """RF014: Blood in vomit."""
        result = run_triage("I vomited blood this morning")
        assert result.outcome == TriageOutcome.URGENT_CARE
        assert any(rf.flag_id == "RF014" for rf in result.red_flags_detected)

    def test_blood_in_stool(self) -> None:
        """RF014: Black stool / melena."""
        result = run_triage("I noticed my stool is black and tarry")
        assert result.outcome == TriageOutcome.URGENT_CARE
        assert any(rf.flag_id == "RF014" for rf in result.red_flags_detected)

    def test_seizure(self) -> None:
        """RF004: Seizure."""
        result = run_triage("I just had a seizure")
        assert result.outcome == TriageOutcome.URGENT_CARE
        assert any(rf.flag_id == "RF004" for rf in result.red_flags_detected)

    def test_breathing_difficulty(self) -> None:
        """RF002: Can't breathe."""
        result = run_triage("I can't breathe properly, shortness of breath")
        assert result.outcome == TriageOutcome.URGENT_CARE
        assert any(rf.flag_id == "RF002" for rf in result.red_flags_detected)

    def test_stroke_symptoms(self) -> None:
        """RF006: Facial drooping, speech difficulty."""
        result = run_triage("My face is drooping on one side and I have slurred speech")
        assert result.outcome == TriageOutcome.URGENT_CARE
        assert any(rf.flag_id == "RF006" for rf in result.red_flags_detected)

    def test_poisoning(self) -> None:
        """RF019: Poisoning / overdose."""
        result = run_triage("I accidentally swallowed too many pills")
        assert result.outcome == TriageOutcome.URGENT_CARE
        assert any(rf.flag_id == "RF019" for rf in result.red_flags_detected)

    def test_severe_allergic_reaction(self) -> None:
        """RF021: Anaphylaxis."""
        result = run_triage("My throat is swelling shut and I can't swallow")
        assert result.outcome == TriageOutcome.URGENT_CARE
        assert any(rf.flag_id == "RF021" for rf in result.red_flags_detected)

    def test_high_fever(self) -> None:
        """RF016: Temperature above 103F / 39.5C."""
        result = run_triage("I have a fever of 104F")
        assert result.outcome == TriageOutcome.URGENT_CARE
        assert any(rf.flag_id == "RF016" for rf in result.red_flags_detected)

    def test_confusion(self) -> None:
        """RF011: Altered mental status."""
        result = run_triage("My father is confused and disoriented suddenly")
        assert result.outcome == TriageOutcome.URGENT_CARE
        assert any(rf.flag_id == "RF011" for rf in result.red_flags_detected)

    def test_head_injury(self) -> None:
        """RF009: Headache after head trauma."""
        result = run_triage("I hit my head in a fall and now have a bad headache")
        assert result.outcome == TriageOutcome.URGENT_CARE
        assert any(rf.flag_id == "RF009" for rf in result.red_flags_detected)


# ═══════════════════════════════════════════════════════════
# Safe (non-escalated) scenarios
# ═══════════════════════════════════════════════════════════

class TestSafeScenarios:
    """Mild symptom queries should NOT trigger escalation."""

    def test_mild_headache(self) -> None:
        ctx = UserContext(age_range=AgeRange.AGE_26_35)
        result = run_triage("I have a mild headache since this morning", user_context=ctx)
        assert result.outcome == TriageOutcome.SELF_CARE

    def test_mild_nausea(self) -> None:
        ctx = UserContext(age_range=AgeRange.AGE_36_45)
        result = run_triage("I am feeling a bit nauseous", user_context=ctx)
        assert result.outcome == TriageOutcome.SELF_CARE

    def test_feeling_tired(self) -> None:
        ctx = UserContext(age_range=AgeRange.AGE_18_25)
        result = run_triage("I am feeling very tired today", user_context=ctx)
        assert result.outcome == TriageOutcome.SELF_CARE

    def test_mild_fever(self) -> None:
        ctx = UserContext(age_range=AgeRange.AGE_46_55)
        result = run_triage("I have a slight fever around 99F", user_context=ctx)
        assert result.outcome == TriageOutcome.SELF_CARE

    def test_indigestion(self) -> None:
        ctx = UserContext(age_range=AgeRange.AGE_36_45)
        result = run_triage("I have some indigestion after lunch", user_context=ctx)
        assert result.outcome == TriageOutcome.SELF_CARE


# ═══════════════════════════════════════════════════════════
# Pattern detection unit tests
# ═══════════════════════════════════════════════════════════

class TestRedFlagPatternDetection:
    """Test individual pattern matching accuracy."""

    def test_detects_chest_pain(self) -> None:
        flags = detect_red_flags("I have chest pain")
        assert any(f.flag_id == "RF001" for f in flags)

    def test_detects_syncope(self) -> None:
        flags = detect_red_flags("I just passed out")
        assert any(f.flag_id == "RF003" for f in flags)

    def test_no_false_positive_for_mild(self) -> None:
        flags = detect_red_flags("mild headache today")
        assert len(flags) == 0

    def test_case_insensitive(self) -> None:
        flags = detect_red_flags("CHEST PAIN AND BREATHING DIFFICULTY")
        assert len(flags) >= 2

    def test_detects_suicidal_ideation(self) -> None:
        flags = detect_red_flags("I want to kill myself")
        assert any(f.flag_id == "RF023" for f in flags)
