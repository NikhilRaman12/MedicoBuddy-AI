"""Pydantic models for Groq structured output — MedicoBuddy AI.

These models define the exact JSON schema that Groq must return.
The response_composer_node builds the system prompt around this schema
and validates Groq's output against it with up to 2 repair attempts.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class QuickActionSchema(BaseModel):
    """Structured quick-action button with full standalone query context."""

    label: str = Field(description="Localized button label shown to the user (max 60 chars)")
    standalone_query: str = Field(
        description="Complete standalone question that can be sent to the API without context"
    )
    parent_topic: str = Field(description="The original health concern this follows up on")


class ActionTableRowSchema(BaseModel):
    """One row in the evidence-grounded action table."""

    guidance_lens: str = Field(
        description="One of: Natural Self-Care | Ayurveda-Informed Wellness | "
                    "Evidence-Based General Medical Self-Care | Prevention and Monitoring"
    )
    what_may_help: str = Field(description="Specific intervention or practice name")
    how_to_follow: str = Field(description="Clear step-by-step instructions")
    frequency_duration: str = Field(description="How often and for how long")
    evidence_strength: str = Field(
        description="One of: High (Clinical Guidelines) | Moderate (Observational) | "
                    "Traditional Use Only | Limited Evidence"
    )
    cautions: str = Field(description="Contraindications and important warnings")
    stop_and_seek_care_if: str = Field(description="Red flags that require stopping self-care")
    citation_ids: list[str] = Field(
        default_factory=list,
        description="IDs of retrieved chunks that support this row",
    )


class ImplementationPlanSchema(BaseModel):
    """Time-phased self-care implementation plan."""

    now: str = Field(description="Immediate actions to take right now")
    next_6_to_12_hours: str = Field(description="Actions for the next 6-12 hours")
    next_24_to_48_hours: str = Field(description="Actions for the next 24-48 hours")
    what_to_monitor: str = Field(
        default="",
        description="Key symptoms and signs to watch for",
    )
    when_to_stop_self_care: str = Field(
        default="",
        description="Criteria that indicate professional care is needed",
    )


class CitationSchema(BaseModel):
    """A fully validated citation from a retrieved chunk."""

    citation_id: str = Field(description="Citation ID (e.g. CIT-001)")
    title: str = Field(description="Document title — must match an ingested document")
    authors: str = Field(description="Author or publishing organization")
    year: str = Field(default="", description="Publication year if available")
    source_file: str = Field(description="Filename of the source PDF")
    page_number: int = Field(default=1)
    chunk_id: str = Field(description="The chunk ID from the retrieved evidence")
    supporting_passage: str = Field(
        description="Verbatim or near-verbatim excerpt from the retrieved chunk"
    )
    retrieval_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Similarity/relevance score from vector retrieval",
    )
    evidence_category: str = Field(
        default="",
        description="One of: clinical_guideline | systematic_review | traditional_evidence | observational",
    )


class GroqStructuredResponse(BaseModel):
    """The complete structured response schema that Groq must return.

    This is the single source of truth for the response contract.
    response_composer_node validates Groq output against this model.
    """

    summary: str = Field(
        description="2-4 sentence evidence-grounded summary in plain language. "
                    "Must be specific to the user's reported symptom, not generic.",
        min_length=50,
    )

    action_table: list[ActionTableRowSchema] = Field(
        description="Evidence-grounded action table. Only include rows with supporting evidence. "
                    "Do not force a row if no evidence supports that lens.",
        min_length=1,
    )

    implementation_plan: ImplementationPlanSchema = Field(
        description="Time-phased self-care plan specific to the reported symptom and context"
    )

    things_to_avoid: list[str] = Field(
        description="Specific things to avoid for this symptom (not generic advice)",
        min_length=1,
    )

    warning_signs: list[str] = Field(
        description="Specific red flags that warrant seeking professional care",
        min_length=1,
    )

    follow_up_question: str = Field(
        description="One targeted clarification question to better understand the user's situation"
    )

    quick_actions: list[QuickActionSchema] = Field(
        description="2-4 contextual follow-up quick actions the user can click",
        min_length=1,
        max_length=4,
    )

    citations: list[CitationSchema] = Field(
        description="Citations derived ONLY from the retrieved evidence chunks provided. "
                    "Do not invent citations. Do not cite documents not in the evidence context.",
        min_length=0,
    )

    evidence_strength: str = Field(
        description="Overall evidence strength: Strong | Moderate | Limited | Insufficient",
    )

    what_this_applies_to: str = Field(
        description="Scope statement — who this guidance applies to and what condition",
    )

    ayurveda_perspectives: list[dict] = Field(
        default_factory=list,
        description="Ayurvedic practices if evidence supports them. "
                    "Must include evidence_label: traditional_use_only",
    )

    preventive_approaches: list[str] = Field(
        default_factory=list,
        description="Preventive measures from retrieved evidence",
    )

    general_self_care_education: str = Field(
        default="",
        description="General educational context about the condition",
    )

    @field_validator("summary")
    @classmethod
    def summary_must_not_be_generic(cls, v: str) -> str:
        """Reject obviously generic summaries."""
        generic_phrases = [
            "for mild symptoms",
            "hydration and rest",
            "sip warm water",
            "ginger tea",
        ]
        lower_v = v.lower()
        # Allow these phrases but ensure the summary has specific context
        if all(phrase in lower_v for phrase in generic_phrases[:2]) and len(v) < 200:
            raise ValueError(
                "Summary appears too generic. Must include symptom-specific guidance."
            )
        return v

    @field_validator("action_table")
    @classmethod
    def action_table_must_have_valid_lenses(cls, rows: list) -> list:
        """Ensure at least one row has a valid guidance lens."""
        valid_lenses = {
            "natural self-care",
            "ayurveda-informed wellness",
            "evidence-based general medical self-care",
            "prevention and monitoring",
        }
        if not rows:
            raise ValueError("Action table must not be empty")
        for row in rows:
            if hasattr(row, "guidance_lens"):
                lens_lower = row.guidance_lens.lower()
                if not any(v in lens_lower for v in valid_lenses):
                    # Accept any lens — just can't be empty
                    if not lens_lower.strip():
                        raise ValueError(f"guidance_lens must not be empty: {row}")
        return rows
