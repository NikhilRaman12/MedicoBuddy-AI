"""Symptom, triage, and severity models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class SeverityLevel(StrEnum):
    """User-reported or inferred symptom severity."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    UNKNOWN = "unknown"


class TriageOutcome(StrEnum):
    """Triage routing decision."""

    SELF_CARE = "self_care"
    CONSULT_CLINICIAN = "consult_clinician"
    URGENT_CARE = "urgent_care"
    OUT_OF_SCOPE = "out_of_scope"


class BodyLocation(StrEnum):
    """Broad body location for symptom reporting."""

    HEAD = "head"
    CHEST = "chest"
    ABDOMEN = "abdomen"
    BACK = "back"
    LIMBS = "limbs"
    GENERAL = "general"  # e.g. fatigue, fever
    OTHER = "other"


class SymptomReport(BaseModel):
    """Structured symptom information gathered during intake."""

    main_symptom: str = Field(description="Primary symptom described by the user")
    body_location: BodyLocation = BodyLocation.GENERAL
    onset_description: str = ""
    duration_description: str = ""
    severity: SeverityLevel = SeverityLevel.UNKNOWN
    progression: str = ""  # e.g. "worsening", "stable", "improving"
    measured_temperature_c: float | None = Field(
        default=None, description="Measured body temperature in Celsius when fever reported"
    )
    hydration_status: str = ""
    can_retain_fluids: bool | None = None
    additional_symptoms: list[str] = Field(default_factory=list)


class RedFlagMatch(BaseModel):
    """A single red-flag pattern that was detected."""

    flag_id: str = Field(description="Unique identifier for the red-flag rule")
    flag_name: str = Field(description="Human-readable name of the red flag")
    matched_terms: list[str] = Field(
        default_factory=list, description="Terms from user input that triggered this flag"
    )
    severity: str = "urgent"
    recommended_action: str = "Seek immediate medical evaluation"


class TriageResult(BaseModel):
    """Output of the deterministic triage engine."""

    outcome: TriageOutcome
    red_flags_detected: list[RedFlagMatch] = Field(default_factory=list)
    scope_issues: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning: str = ""
    emergency_contact: dict[str, str] | None = None
