"""Response contract model enforcing the required 9-part MedicoBuddy AI answer structure."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from medicobuddy.models.evidence import EvidenceClaim, EvidenceLevel
from medicobuddy.models.symptom import TriageOutcome


class Citation(BaseModel):
    """Claim-linked citation with exact passage location and limitation."""

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


class AyurvedaPerspective(BaseModel):
    """Ayurveda-informed non-pharmacological wellness perspective."""

    practice: str = Field(description="The lifestyle/wellness practice")
    description: str = ""
    evidence_label: str = Field(
        default="evidence_supported",
        description="One of: evidence_supported, limited_preliminary, traditional_use_only, conflicting"
    )
    source_summary: str = ""


class ActionTableRow(BaseModel):
    """Row in the required Action Table matching exact 7 columns + citation IDs."""

    guidance_lens: str = Field(description="Natural self-care / Ayurveda-informed wellness / General medical self-care")
    what_may_help: str
    how_to_follow: str
    frequency_duration: str = ""
    frequency_or_duration: str = ""
    evidence_level: str = "Moderate"
    important_cautions: str = ""
    cautions: str = ""
    stop_and_seek_care_if: str = ""
    citation_ids: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.frequency_duration and self.frequency_or_duration:
            self.frequency_duration = self.frequency_or_duration
        elif not self.frequency_or_duration and self.frequency_duration:
            self.frequency_or_duration = self.frequency_duration

        if not self.important_cautions and self.cautions:
            self.important_cautions = self.cautions
        elif not self.cautions and self.important_cautions:
            self.cautions = self.important_cautions


class ImplementationPlan(BaseModel):
    """Simple implementation plan for Now, Next 6-12h, Next 24-48h."""

    now: str = ""
    next_6_to_12_hours: str = ""
    next_24_to_48_hours: str = ""


class AvoidAndMonitorRow(BaseModel):
    """Row in the Avoid and Monitor table."""

    what_to_avoid: str = ""
    why_avoid: str = ""
    what_to_monitor: str = ""
    monitoring_frequency: str = ""


class MedicoBuddyResponseDraft(BaseModel):
    """Pydantic draft response model for ChatGroq structured output."""

    what_this_applies_to: str = Field(description="Exact scope and symptom summary")
    summary: str = Field(default="", description="Plain-language evidence-grounded summary")
    action_table: list[ActionTableRow] = Field(default_factory=list, description="Evidence-backed non-pharmacological self-care action rows")
    implementation_plan: ImplementationPlan = Field(default_factory=ImplementationPlan, description="Step-by-step timeline (now, next 6-12h, next 24-48h)")
    avoid_and_monitor: list[AvoidAndMonitorRow] = Field(default_factory=list, description="What to avoid and what symptoms to monitor")
    when_to_seek_care: list[str] = Field(default_factory=list, description="Red flag thresholds when to seek professional care")
    targeted_follow_up: str = Field(default="Are you experiencing any other symptoms?", description="One targeted follow-up question")
    follow_up_question: str = Field(default="", description="One relevant follow-up question")


class MedicoBuddyResponse(BaseModel):
    """The full required answer contract."""

    # 1. Safety status
    triage_outcome: TriageOutcome
    safety_status: str = Field(
        description="One of: self-care information, professional review advised, urgent care, emergency, out of scope, insufficient evidence"
    )

    # 2. What this information applies to
    what_this_applies_to: str = ""

    # Summary
    summary: str = ""

    # 3. Action table
    action_table: list[ActionTableRow] = Field(default_factory=list)

    # 4. Simple implementation plan
    implementation_plan: ImplementationPlan = Field(default_factory=ImplementationPlan)

    # 5. Avoid and monitor table
    avoid_and_monitor: list[AvoidAndMonitorRow] = Field(default_factory=list)

    # 6. When to seek professional help
    when_to_seek_care: list[str] = Field(default_factory=list)

    # 7. Evidence and limitations
    citations: list[Citation] = Field(default_factory=list)
    overall_evidence_level: EvidenceLevel = EvidenceLevel.INSUFFICIENT

    # 8. One targeted follow-up question
    targeted_follow_up: str = ""
    follow_up_question: str = ""

    # 9. Educational-use statement
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
    ayurveda_perspectives: list[dict[str, Any]] = Field(default_factory=list)
    things_to_avoid: list[str] = Field(default_factory=list)
    monitoring_guidance: list[str] = Field(default_factory=list)
    seek_care_conditions: list[str] = Field(default_factory=list)
    disclaimer: str = ""
    emergency_message: str = ""
    emergency_contact: dict[str, str] | None = None
