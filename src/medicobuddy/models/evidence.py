"""Evidence, study reference, and source quality models."""

from __future__ import annotations

from datetime import datetime
from enum import IntEnum, StrEnum

from pydantic import BaseModel, Field


class EvidenceLevel(StrEnum):
    """Evidence strength classification."""

    HIGH = "high"
    MODERATE = "moderate"
    LIMITED = "limited"
    INSUFFICIENT = "insufficient"
    CONFLICTING = "conflicting"


class SourceTier(IntEnum):
    """Evidence hierarchy tier (1 = highest quality)."""

    CLINICAL_GUIDELINE = 1
    SYSTEMATIC_REVIEW = 2
    RCT = 3
    COHORT_OBSERVATIONAL = 4
    CASE_REPORT = 5
    EXPERT_CONSENSUS = 6
    BLOG_POPULAR = 7


class StudyDesign(StrEnum):
    """Type of study design."""

    SYSTEMATIC_REVIEW = "systematic_review"
    META_ANALYSIS = "meta_analysis"
    RCT = "randomized_controlled_trial"
    COHORT = "cohort_study"
    CASE_CONTROL = "case_control"
    CROSS_SECTIONAL = "cross_sectional"
    CASE_REPORT = "case_report"
    GUIDELINE = "clinical_guideline"
    EXPERT_OPINION = "expert_opinion"
    TRADITIONAL_TEXT = "traditional_text"
    NARRATIVE_REVIEW = "narrative_review"
    BLOG = "blog_article"
    UNKNOWN = "unknown"


class AyurvedaEvidenceCategory(StrEnum):
    """Evidence classification for Ayurvedic claims."""

    EVIDENCE_SUPPORTED = "evidence_supported"
    LIMITED_PRELIMINARY = "limited_or_preliminary_evidence"
    TRADITIONAL_INSUFFICIENT = "traditional_use_insufficient_clinical_evidence"
    EVIDENCE_OF_RISK = "evidence_of_risk"
    CONFLICTING = "conflicting_evidence"


class RetractionStatus(StrEnum):
    """Publication retraction status."""

    NONE = "none"
    RETRACTED = "retracted"
    CORRECTED = "corrected"
    EXPRESSION_OF_CONCERN = "expression_of_concern"
    UNKNOWN = "unknown"


class StudyReference(BaseModel):
    """A reference to a specific study or publication."""

    title: str
    authors: list[str] = Field(default_factory=list)
    issuing_organization: str = ""
    publication_date: str = ""
    doi: str = ""
    pmid: str = ""
    trial_id: str = ""
    canonical_url: str = ""
    study_design: StudyDesign = StudyDesign.UNKNOWN
    population: str = ""
    sample_size: int | None = None
    intervention: str = ""
    outcome_summary: str = ""
    limitations: str = ""
    retraction_status: RetractionStatus = RetractionStatus.UNKNOWN
    source_tier: SourceTier = SourceTier.BLOG_POPULAR
    retrieval_timestamp: datetime | None = None
    supporting_passage: str = ""
    usage_licence: str = ""
    conflicts_of_interest: str = ""


class EvidenceClaim(BaseModel):
    """A single evidence-backed claim with provenance."""

    claim_id: str = Field(default="", description="Unique identifier for this claim")
    claim_text: str = Field(description="The factual claim being made")
    evidence_level: EvidenceLevel = EvidenceLevel.INSUFFICIENT
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    supporting_studies: list[StudyReference] = Field(default_factory=list)
    contradicting_studies: list[StudyReference] = Field(default_factory=list)
    ayurveda_category: AyurvedaEvidenceCategory | None = None
    limitations_summary: str = ""
    population_applicability: str = ""
    last_reviewed: datetime | None = None


class EvidenceScore(BaseModel):
    """Composite score for a piece of evidence."""

    study_design_score: float = 0.0
    bias_risk_score: float = 0.0
    sample_size_score: float = 0.0
    recency_score: float = 0.0
    directness_score: float = 0.0
    replication_score: float = 0.0
    retraction_penalty: float = 0.0
    population_relevance_score: float = 0.0
    safety_reporting_score: float = 0.0
    conflict_of_interest_penalty: float = 0.0
    composite_score: float = 0.0

    def compute_composite(self) -> float:
        """Weighted composite of all sub-scores minus penalties."""
        weights = {
            "study_design": 0.20,
            "bias_risk": 0.15,
            "sample_size": 0.10,
            "recency": 0.10,
            "directness": 0.15,
            "replication": 0.10,
            "population": 0.10,
            "safety": 0.10,
        }
        raw = (
            self.study_design_score * weights["study_design"]
            + self.bias_risk_score * weights["bias_risk"]
            + self.sample_size_score * weights["sample_size"]
            + self.recency_score * weights["recency"]
            + self.directness_score * weights["directness"]
            + self.replication_score * weights["replication"]
            + self.population_relevance_score * weights["population"]
            + self.safety_reporting_score * weights["safety"]
        )
        self.composite_score = max(0.0, raw - self.retraction_penalty - self.conflict_of_interest_penalty)
        return self.composite_score
