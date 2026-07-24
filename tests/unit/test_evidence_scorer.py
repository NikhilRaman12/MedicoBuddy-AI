"""Tests for evidence scoring and Ayurveda classification."""

from __future__ import annotations

import pytest

from medicobuddy.evidence.scorer import (
    classify_ayurveda_evidence,
    determine_evidence_level,
    score_study,
)
from medicobuddy.models.evidence import (
    AyurvedaEvidenceCategory,
    EvidenceLevel,
    EvidenceScore,
    RetractionStatus,
    SourceTier,
    StudyDesign,
    StudyReference,
)


class TestEvidenceScoring:
    """Test multi-factor evidence scoring."""

    def test_systematic_review_scores_high(self) -> None:
        ref = StudyReference(
            title="SR: Hydration and Headache",
            study_design=StudyDesign.SYSTEMATIC_REVIEW,
            source_tier=SourceTier.SYSTEMATIC_REVIEW,
            sample_size=2000,
            publication_date="2024",
            retraction_status=RetractionStatus.NONE,
        )
        score = score_study(ref)
        assert score.composite_score > 0.5

    def test_blog_scores_very_low(self) -> None:
        ref = StudyReference(
            title="Blog post about headaches",
            study_design=StudyDesign.BLOG,
            source_tier=SourceTier.BLOG_POPULAR,
            retraction_status=RetractionStatus.NONE,
        )
        score = score_study(ref)
        assert score.composite_score < 0.2

    def test_retracted_paper_penalized(self) -> None:
        ref = StudyReference(
            title="Retracted study",
            study_design=StudyDesign.RCT,
            source_tier=SourceTier.RCT,
            retraction_status=RetractionStatus.RETRACTED,
            sample_size=500,
            publication_date="2023",
        )
        score = score_study(ref)
        assert score.retraction_penalty == 1.0
        assert score.composite_score == 0.0

    def test_recent_study_scores_higher_recency(self) -> None:
        recent = StudyReference(
            title="Recent",
            study_design=StudyDesign.COHORT,
            publication_date="2025",
            retraction_status=RetractionStatus.NONE,
        )
        old = StudyReference(
            title="Old",
            study_design=StudyDesign.COHORT,
            publication_date="2005",
            retraction_status=RetractionStatus.NONE,
        )
        assert score_study(recent).recency_score > score_study(old).recency_score


class TestEvidenceLevelDetermination:
    """Test overall evidence level calculation."""

    def test_no_evidence_is_insufficient(self) -> None:
        assert determine_evidence_level([]) == EvidenceLevel.INSUFFICIENT

    def test_all_retracted_is_insufficient(self) -> None:
        scores = [EvidenceScore(retraction_penalty=1.0, composite_score=0.0)]
        assert determine_evidence_level(scores) == EvidenceLevel.INSUFFICIENT


class TestAyurvedaClassification:
    """Test Ayurveda evidence classification."""

    def test_no_studies_is_traditional(self) -> None:
        result = classify_ayurveda_evidence([])
        assert result == AyurvedaEvidenceCategory.TRADITIONAL_INSUFFICIENT

    def test_risk_evidence_flagged(self) -> None:
        refs = [
            StudyReference(
                title="Adverse effects study",
                study_design=StudyDesign.RCT,
                outcome_summary="Significant adverse risk observed",
                retraction_status=RetractionStatus.NONE,
            )
        ]
        result = classify_ayurveda_evidence(refs)
        assert result == AyurvedaEvidenceCategory.EVIDENCE_OF_RISK

    def test_sr_without_contradiction_is_supported(self) -> None:
        refs = [
            StudyReference(
                title="Positive SR",
                study_design=StudyDesign.SYSTEMATIC_REVIEW,
                outcome_summary="Beneficial effect observed",
                retraction_status=RetractionStatus.NONE,
            )
        ]
        result = classify_ayurveda_evidence(refs)
        assert result == AyurvedaEvidenceCategory.EVIDENCE_SUPPORTED
