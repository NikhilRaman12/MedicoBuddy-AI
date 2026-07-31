"""Response contract model enforcing the required 12-part MedicoBuddy AI answer structure.

Every successful answer must contain all 12 mandatory sections as specified.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from medicobuddy.models.evidence import EvidenceClaim, EvidenceLevel
from medicobuddy.models.symptom import TriageOutcome


class Citation(BaseModel):
    """Claim-linked citation with document title and PDF page number."""

    number: int = 1
    citation_id: str = ""
    title: str = ""
    authors: str = ""
    publisher: str = ""
    publication_date: str = ""
    retrieved_at: str = ""
    url: str = ""
    doi: str = ""
    pmid: str = ""
    passage_id: str = ""
    evidence_type: str = ""
    source_type: str = ""
    supporting_passage: str = ""
    retrieval_date: str = ""
    limitation: str = ""
    page_number: int | None = None
    source_file: str = ""


class AyurvedaPerspective(BaseModel):
    """Ayurveda-informed non-pharmacological wellness perspective with explicit evidence label."""

    practice: str = Field(description="The lifestyle/wellness practice")
    description: str = ""
    evidence_label: str = Field(
        default="traditional_use_only",
        description="One of: evidence_supported, limited_preliminary, traditional_use_only, conflicting"
    )
    source_summary: str = ""


class ActionTableRow(BaseModel):
    """Row in the required responsive table matching spec column names.

    | Guidance lens | What may help | How to follow | Evidence strength | Cautions | Citation |
    """

    guidance_lens: str = Field(description="Natural self-care / Ayurveda-informed wellness / General medical self-care")
    what_may_help: str
    how_to_follow: str
    frequency_duration: str = ""
    evidence_strength: str = "Moderate"
    evidence_level: str = "Moderate"  # backward compat
    cautions: str = ""
    important_cautions: str = ""  # backward compat
    stop_and_seek_care_if: str = ""
    citation_ids: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.evidence_strength and self.evidence_level:
            self.evidence_strength = self.evidence_level
        elif not self.evidence_level and self.evidence_strength:
            self.evidence_level = self.evidence_strength

        if not self.cautions and self.important_cautions:
            self.cautions = self.important_cautions
        elif not self.important_cautions and self.cautions:
            self.important_cautions = self.cautions


class ImplementationPlan(BaseModel):
    """Implementation plan: now, next 6-12 hours, next 24-48 hours."""

    now: str = ""
    next_6_to_12_hours: str = ""
    next_24_to_48_hours: str = ""


class AvoidAndMonitorRow(BaseModel):
    """Row in the Things to Avoid / Monitor table."""

    what_to_avoid: str = ""
    why_avoid: str = ""
    what_to_monitor: str = ""
    monitoring_frequency: str = ""


class QuickAction(BaseModel):
    """Structured contextual quick action button definition matching spec #7."""

    action_id: str = Field(default="", description="Unique ID for the follow-up action")
    label: str = Field(description="Short user-facing button label")
    standalone_query: str = Field(description="Full query including parent topic context")
    intent: str = Field(default="general_followup", description="Follow-up intent category")
    parent_topic: str = Field(default="general_health", description="Parent health topic identifier")


class MedicoBuddyResponse(BaseModel):
    """The full required 12-part answer contract."""

    # 1. Safety status
    triage_outcome: TriageOutcome
    safety_status: str = Field(
        description="One of: self-care information, professional review advised, urgent care, emergency, out of scope, insufficient evidence"
    )

    # 2. What this information applies to + evidence-grounded explanation
    what_this_applies_to: str = ""
    summary: str = ""

    # 3. Responsive action table
    action_table: list[ActionTableRow] = Field(default_factory=list)

    # 4. Natural preventive approaches
    preventive_approaches: list[str] = Field(default_factory=list)

    # 5. Traditional Ayurvedic context (explicitly labelled by evidence level)
    ayurveda_perspectives: list[AyurvedaPerspective] = Field(default_factory=list)

    # 6. General non-prescriptive medical self-care education
    general_self_care_education: str = ""

    # 7. Implementation plan
    implementation_plan: ImplementationPlan = Field(default_factory=ImplementationPlan)

    # 8. What to avoid
    things_to_avoid: list[str] = Field(default_factory=list)
    avoid_and_monitor: list[AvoidAndMonitorRow] = Field(default_factory=list)

    # 9. Warning signs and when to seek professional care
    when_to_seek_care: list[str] = Field(default_factory=list)
    warning_signs: list[str] = Field(default_factory=list)

    # 10. Verified sources with document title and PDF page number
    citations: list[Citation] = Field(default_factory=list)
    overall_evidence_level: EvidenceLevel = EvidenceLevel.INSUFFICIENT

    # 11. One follow-up question only when required
    targeted_follow_up: str = ""
    follow_up_question: str = ""

    # 12. Contextual quick-action chips and buttons
    quick_action_chips: list[str] = Field(default_factory=list)
    quick_actions: list[QuickAction] = Field(default_factory=list)

    # Educational-use statement (always present)
    educational_statement: str = Field(
        default=(
            "Educational-use statement: MedicoBuddy AI provides evidence-grounded general self-care education for adults aged 18–65. "
            "It does not diagnose, cure, prescribe, recommend medicines, or replace professional healthcare evaluation."
        )
    )

    # Legacy attributes for backward compatibility
    urgency_summary: str = ""
    user_report_summary: str = ""
    safe_comfort_steps: list[str] = Field(default_factory=list)
    monitoring_guidance: list[str] = Field(default_factory=list)
    seek_care_conditions: list[str] = Field(default_factory=list)
    disclaimer: str = ""
    emergency_message: str = ""
    emergency_contact: dict[str, str] | None = None
