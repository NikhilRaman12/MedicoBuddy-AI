"""Response contract model — the 10-section MedicoBuddy response."""

from __future__ import annotations

from pydantic import BaseModel, Field

from medicobuddy.models.evidence import EvidenceClaim, EvidenceLevel
from medicobuddy.models.symptom import TriageOutcome


class Citation(BaseModel):
    """A numbered citation with a clickable link."""

    number: int
    title: str
    authors: str = ""
    publication_date: str = ""
    url: str = ""
    doi: str = ""
    pmid: str = ""
    source_type: str = ""


class AyurvedaPerspective(BaseModel):
    """Ayurveda-informed non-pharmacological wellness perspective."""

    practice: str = Field(description="The lifestyle/wellness practice")
    description: str = ""
    evidence_label: str = Field(
        description="One of: evidence_supported, limited_preliminary, "
        "traditional_insufficient, evidence_of_risk, conflicting"
    )
    source_summary: str = ""


class MedicoBuddyResponse(BaseModel):
    """The full 10-section response contract.

    Every response follows this structure regardless of triage outcome.
    """

    # 1. Scope / urgency status
    triage_outcome: TriageOutcome
    urgency_summary: str = Field(
        description="Brief urgency label: self-care information / contact a clinician / urgent care"
    )

    # 2. Neutral summary of what the user reported
    user_report_summary: str = ""

    # 3. Safe comfort steps
    safe_comfort_steps: list[str] = Field(
        default_factory=list,
        description="Low-risk measures: rest, hydration, positioning, breathing, etc.",
    )

    # 4. Ayurveda-informed perspective (clearly labelled)
    ayurveda_perspectives: list[AyurvedaPerspective] = Field(default_factory=list)

    # 5. What to avoid
    things_to_avoid: list[str] = Field(default_factory=list)

    # 6. What changes to monitor
    monitoring_guidance: list[str] = Field(default_factory=list)

    # 7. When to seek professional / urgent care
    seek_care_conditions: list[str] = Field(default_factory=list)

    # 8. Evidence confidence
    overall_evidence_level: EvidenceLevel = EvidenceLevel.INSUFFICIENT
    evidence_claims: list[EvidenceClaim] = Field(default_factory=list)

    # 9. Citations
    citations: list[Citation] = Field(default_factory=list)

    # 10. Disclaimer
    disclaimer: str = Field(
        default=(
            "MedicoBuddy provides general wellness information for educational purposes only. "
            "It does not diagnose conditions, prescribe treatments, or replace professional "
            "medical advice. Always consult a qualified healthcare provider for medical concerns."
        )
    )

    # ── Emergency escalation (populated when red flags detected) ──
    emergency_message: str = ""
    emergency_contact: dict[str, str] | None = None
