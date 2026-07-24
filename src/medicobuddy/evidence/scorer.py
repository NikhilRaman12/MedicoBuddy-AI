"""Multi-factor evidence scoring implementation."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from medicobuddy.models.evidence import (
    AyurvedaEvidenceCategory,
    EvidenceLevel,
    EvidenceScore,
    RetractionStatus,
    SourceTier,
    StudyDesign,
    StudyReference,
)
from medicobuddy.models.mcp import MCPResult

logger = logging.getLogger(__name__)

# ── Study design score mapping ───────────────────────────────
DESIGN_SCORES: dict[str, float] = {
    StudyDesign.SYSTEMATIC_REVIEW: 1.0,
    StudyDesign.META_ANALYSIS: 1.0,
    StudyDesign.RCT: 0.85,
    StudyDesign.COHORT: 0.65,
    StudyDesign.CASE_CONTROL: 0.55,
    StudyDesign.CROSS_SECTIONAL: 0.50,
    StudyDesign.CASE_REPORT: 0.30,
    StudyDesign.GUIDELINE: 0.95,
    StudyDesign.EXPERT_OPINION: 0.25,
    StudyDesign.TRADITIONAL_TEXT: 0.15,
    StudyDesign.NARRATIVE_REVIEW: 0.40,
    StudyDesign.BLOG: 0.05,
    StudyDesign.UNKNOWN: 0.10,
}


def score_study(study: StudyReference) -> EvidenceScore:
    """Score a single study across all evidence dimensions.

    Args:
        study: StudyReference to score.

    Returns:
        EvidenceScore with all sub-scores and composite.
    """
    score = EvidenceScore()

    # 1. Study design
    score.study_design_score = DESIGN_SCORES.get(study.study_design, 0.1)

    # 2. Risk of bias (simplified heuristic)
    if study.study_design in {StudyDesign.SYSTEMATIC_REVIEW, StudyDesign.META_ANALYSIS, StudyDesign.GUIDELINE}:
        score.bias_risk_score = 0.9
    elif study.study_design == StudyDesign.RCT:
        score.bias_risk_score = 0.8
    elif study.study_design in {StudyDesign.COHORT, StudyDesign.CASE_CONTROL}:
        score.bias_risk_score = 0.5
    elif study.study_design == StudyDesign.BLOG:
        score.bias_risk_score = 0.05
    else:
        score.bias_risk_score = 0.2

    # 3. Sample size
    if study.sample_size is not None:
        if study.sample_size >= 1000:
            score.sample_size_score = 1.0
        elif study.sample_size >= 100:
            score.sample_size_score = 0.7
        elif study.sample_size >= 30:
            score.sample_size_score = 0.4
        else:
            score.sample_size_score = 0.2
    else:
        score.sample_size_score = 0.1

    # 4. Recency
    if study.publication_date:
        try:
            year = int(study.publication_date[:4])
            current_year = datetime.now(timezone.utc).year
            age = current_year - year
            if age <= 2:
                score.recency_score = 1.0
            elif age <= 5:
                score.recency_score = 0.8
            elif age <= 10:
                score.recency_score = 0.6
            else:
                score.recency_score = 0.3
        except (ValueError, IndexError):
            score.recency_score = 0.2
    else:
        score.recency_score = 0.1

    # 5. Directness
    score.directness_score = 0.05 if study.study_design == StudyDesign.BLOG else 0.5

    # 6. Replication (not assessable from single study — default)
    score.replication_score = 0.3

    # 7. Retraction penalty
    if study.retraction_status == RetractionStatus.RETRACTED:
        score.retraction_penalty = 1.0  # Complete disqualification
    elif study.retraction_status == RetractionStatus.EXPRESSION_OF_CONCERN:
        score.retraction_penalty = 0.5
    elif study.retraction_status == RetractionStatus.CORRECTED:
        score.retraction_penalty = 0.1
    else:
        score.retraction_penalty = 0.0

    # 8. Population relevance (default — needs user context)
    score.population_relevance_score = 0.5

    # 9. Safety reporting
    if study.limitations:
        score.safety_reporting_score = 0.6
    else:
        score.safety_reporting_score = 0.3

    # 10. Conflicts of interest
    if study.conflicts_of_interest and "none" not in study.conflicts_of_interest.lower():
        score.conflict_of_interest_penalty = 0.15
    else:
        score.conflict_of_interest_penalty = 0.0

    score.compute_composite()
    return score


def mcp_result_to_study_ref(result: MCPResult) -> StudyReference:
    """Convert an MCPResult into a StudyReference for scoring."""
    # Map MCPResult study_type string to StudyDesign enum
    design_map: dict[str, StudyDesign] = {
        "meta_analysis": StudyDesign.META_ANALYSIS,
        "systematic_review": StudyDesign.SYSTEMATIC_REVIEW,
        "randomized_controlled_trial": StudyDesign.RCT,
        "clinical_trial": StudyDesign.RCT,
        "cohort_study": StudyDesign.COHORT,
        "case_report": StudyDesign.CASE_REPORT,
        "clinical_guideline": StudyDesign.GUIDELINE,
        "narrative_review": StudyDesign.NARRATIVE_REVIEW,
        "consumer_health_resource": StudyDesign.GUIDELINE,
    }
    design = design_map.get(result.study_type, StudyDesign.UNKNOWN)

    retraction_map: dict[str, RetractionStatus] = {
        "none": RetractionStatus.NONE,
        "retracted": RetractionStatus.RETRACTED,
        "corrected": RetractionStatus.CORRECTED,
    }
    retraction = retraction_map.get(result.retraction_status, RetractionStatus.UNKNOWN)

    return StudyReference(
        title=result.title,
        authors=result.authors,
        issuing_organization=result.issuing_organization,
        publication_date=result.publication_date,
        doi=result.doi,
        pmid=result.pmid,
        trial_id=result.trial_id,
        canonical_url=result.canonical_url,
        study_design=design,
        population=result.population,
        sample_size=result.sample_size,
        intervention=result.intervention,
        outcome_summary=result.outcome,
        limitations=result.limitations,
        retraction_status=retraction,
        source_tier=SourceTier(result.source_quality_tier),
        retrieval_timestamp=result.retrieval_timestamp,
        supporting_passage=result.supporting_passage,
        usage_licence=result.usage_licence,
    )


def determine_evidence_level(scores: list[EvidenceScore]) -> EvidenceLevel:
    """Determine overall evidence level from scored studies.

    Args:
        scores: List of EvidenceScore objects.

    Returns:
        Aggregate EvidenceLevel.
    """
    if not scores:
        return EvidenceLevel.INSUFFICIENT

    # Filter out retracted
    valid = [s for s in scores if s.retraction_penalty < 1.0]
    if not valid:
        return EvidenceLevel.INSUFFICIENT

    avg = sum(s.composite_score for s in valid) / len(valid)
    max_score = max(s.composite_score for s in valid)

    if max_score >= 0.7 and avg >= 0.5:
        return EvidenceLevel.HIGH
    if max_score >= 0.5 and avg >= 0.35:
        return EvidenceLevel.MODERATE
    if max_score >= 0.3:
        return EvidenceLevel.LIMITED
    return EvidenceLevel.INSUFFICIENT


def classify_ayurveda_evidence(
    study_refs: list[StudyReference],
) -> AyurvedaEvidenceCategory:
    """Classify Ayurvedic claims into evidence categories.

    Never converts 'traditional use' into 'proven effective'.
    """
    if not study_refs:
        return AyurvedaEvidenceCategory.TRADITIONAL_INSUFFICIENT

    has_rct = any(s.study_design == StudyDesign.RCT for s in study_refs)
    has_sr = any(
        s.study_design in {StudyDesign.SYSTEMATIC_REVIEW, StudyDesign.META_ANALYSIS}
        for s in study_refs
    )
    has_risk = any(
        "risk" in (s.outcome_summary or "").lower() or "adverse" in (s.outcome_summary or "").lower()
        for s in study_refs
    )
    has_contradiction = any(
        "no effect" in (s.outcome_summary or "").lower()
        or "not effective" in (s.outcome_summary or "").lower()
        for s in study_refs
    )

    if has_risk:
        return AyurvedaEvidenceCategory.EVIDENCE_OF_RISK
    if has_contradiction and (has_rct or has_sr):
        return AyurvedaEvidenceCategory.CONFLICTING
    if has_sr and not has_contradiction:
        return AyurvedaEvidenceCategory.EVIDENCE_SUPPORTED
    if has_rct and not has_contradiction:
        return AyurvedaEvidenceCategory.LIMITED_PRELIMINARY
    return AyurvedaEvidenceCategory.TRADITIONAL_INSUFFICIENT
