"""Semantic document chunking, medical-scope filtering, and provenance tracking."""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from medicobuddy.evidence.parser import ParsedDocument
from medicobuddy.safety.prompt_injection import check_retrieved_document

logger = logging.getLogger(__name__)

# Token estimation (~4 characters per token)
# Spec: chunk size: 700–900 tokens (2800–3600 chars), overlap: 100–150 tokens (400–600 chars)
DEFAULT_CHUNK_SIZE_CHARS = 3200
DEFAULT_OVERLAP_CHARS = 500
MIN_USEFUL_TEXT_CHARS = 100

PROHIBITED_TERMS = {
    "cure for cancer",
    "ingest essential oil",
    "pure essential oil orally",
    "stop medical treatment",
    "do not consult a doctor",
    "rx prescription without doctor",
}

# Exclusion terms for clinician/surgical/prescriptive content
OUT_OF_SCOPE_TERMS = [
    r"\bsurgery\b", r"\bsurgical\b", r"\boperative\b", r"\bincision\b",
    r"\bprescription\b", r"\bprescribe\b", r"\bdosage:\b", r"\bmg/kg\b",
    r"\bpanchakarma\b", r"\bvamana\b", r"\bvirechana\b", r"\bbasti\b",
    r"\bnasya with\b", r"\bdiagnosis instructions\b", r"\bphysician-only\b",
    r"\btreatment protocol\b", r"\bchemotherapy\b", r"\bradiation therapy\b"
]


@dataclass
class EvidenceChunk:
    """Standardised evidence chunk with complete provenance metadata matching spec."""

    chunk_id: str
    document_id: str
    text: str
    title: str
    publisher: str
    source_url: str
    source_file: str
    page_number: int | None
    section_title: str
    publication_date: str | None
    retrieval_date: str
    licence: str
    evidence_type: str
    evidence_lane: str
    retrieval_allowed: bool
    checksum: str
    authors: list[str] = field(default_factory=list)
    study_type: str = "Systematic Review"
    population: str = "adults_18_65"
    evidence_tier: int = 1
    retraction_status: str = "active"
    quarantined: bool = False
    quarantine_reason: str = ""

    def to_metadata(self) -> dict[str, Any]:
        """Convert chunk into vector store metadata dictionary matching exact spec schema."""
        d = asdict(self)
        d["doc_id"] = self.document_id
        d["authors"] = ", ".join(self.authors) if isinstance(self.authors, list) else str(self.authors)
        return d


class DocumentChunker:
    """Chunks documents into token-aware passages and applies medical-scope filtering."""

    @staticmethod
    def classify_evidence_lane(text: str, source_file: str) -> tuple[str, bool]:
        """Classify passage into evidence lane and determine retrieval_allowed flag.

        Lanes:
        - GENERAL_SELF_CARE
        - NATURAL_WELLNESS
        - AYURVEDA_TRADITIONAL_USE
        - SAFETY_AND_CONTRAINDICATION
        - RED_FLAG_AND_ESCALATION
        - OUT_OF_SCOPE_CLINICIAN_CONTENT
        """
        text_lower = text.lower()

        # Check for out-of-scope clinical/surgical/prescription content
        for pattern in OUT_OF_SCOPE_TERMS:
            if re.search(pattern, text_lower):
                return "OUT_OF_SCOPE_CLINICIAN_CONTENT", False

        # Check red flag & escalation
        if any(term in text_lower for term in ["red flag", "emergency", "immediate medical attention", "thunderclap", "cyanosis"]):
            return "RED_FLAG_AND_ESCALATION", True

        # Check safety & contraindications
        if any(term in text_lower for term in ["contraindication", "caution", "safety rule", "herb-drug interaction", "side effect"]):
            return "SAFETY_AND_CONTRAINDICATION", True

        # Check Ayurveda traditional use
        if "ayurveda" in source_file.lower() or "ccras" in source_file.lower() or "dinacharya" in text_lower:
            return "AYURVEDA_TRADITIONAL_USE", True

        # Check natural wellness
        if any(term in text_lower for term in ["herbal", "natural remedy", "tea", "compress", "saline"]):
            return "NATURAL_WELLNESS", True

        return "GENERAL_SELF_CARE", True

    @staticmethod
    def chunk_document(
        doc: ParsedDocument,
        chunk_size_chars: int = DEFAULT_CHUNK_SIZE_CHARS,
        overlap_chars: int = DEFAULT_OVERLAP_CHARS,
    ) -> list[EvidenceChunk]:
        """Convert a ParsedDocument into provenance-preserving EvidenceChunks."""
        chunks: list[EvidenceChunk] = []
        chunk_idx = 1

        # Retracted document handling
        if doc.retraction_status == "retracted" or doc.quarantined:
            logger.warning("Document %s is quarantined/retracted — producing quarantined chunk", doc.doc_id)
            return [
                EvidenceChunk(
                    chunk_id=f"CHK_{doc.checksum[:8]}_1",
                    document_id=doc.doc_id,
                    text=f"Quarantined/Retracted Document: {doc.title} — {doc.quarantine_reason}",
                    title=doc.title,
                    publisher=doc.publisher,
                    source_url=doc.url,
                    source_file=doc.source_file,
                    page_number=1,
                    section_title="Quarantined",
                    publication_date=doc.publication_date,
                    retrieval_date=doc.retrieval_date,
                    licence=doc.licence,
                    evidence_type="consumer guidance",
                    evidence_lane="SAFETY_AND_CONTRAINDICATION",
                    retrieval_allowed=False,
                    checksum=doc.checksum,
                    quarantined=True,
                    quarantine_reason=doc.quarantine_reason or "Retracted document",
                )
            ]

        for sec in doc.sections:
            sec_text = sec.content.strip()
            if len(sec_text) < MIN_USEFUL_TEXT_CHARS:
                continue

            sub_passages = DocumentChunker._split_text(sec_text, chunk_size_chars, overlap_chars)
            for passage in sub_passages:
                if len(passage.strip()) < MIN_USEFUL_TEXT_CHARS:
                    continue

                chunk_id = f"CHK_{doc.checksum[:8]}_{chunk_idx}"
                evidence_lane, retrieval_allowed = DocumentChunker.classify_evidence_lane(passage, doc.source_file)
                quarantined = False
                quarantine_reason = ""

                # Prompt injection check
                injection_check = check_retrieved_document(passage)
                if not injection_check.is_safe:
                    quarantined = True
                    retrieval_allowed = False
                    quarantine_reason = f"Prompt injection detected: {injection_check.detected_patterns}"

                # Prohibited claims check
                passage_lower = passage.lower()
                for term in PROHIBITED_TERMS:
                    if term in passage_lower:
                        quarantined = True
                        retrieval_allowed = False
                        quarantine_reason = f"Prohibited clinical claim detected: {term}"
                        break

                chunks.append(
                    EvidenceChunk(
                        chunk_id=chunk_id,
                        document_id=doc.doc_id,
                        text=passage,
                        title=doc.title,
                        publisher=doc.publisher,
                        source_url=doc.url,
                        source_file=doc.source_file,
                        page_number=sec.page_number or 1,
                        section_title=sec.section_title,
                        publication_date=doc.publication_date,
                        retrieval_date=doc.retrieval_date,
                        licence=doc.licence,
                        evidence_type="guideline" if doc.evidence_tier == 1 else "consumer guidance",
                        evidence_lane=evidence_lane,
                        retrieval_allowed=retrieval_allowed,
                        checksum=doc.checksum,
                        authors=doc.authors,
                        study_type=doc.study_type,
                        population=doc.population,
                        evidence_tier=doc.evidence_tier,
                        retraction_status=doc.retraction_status,
                        quarantined=quarantined,
                        quarantine_reason=quarantine_reason,
                    )
                )
                chunk_idx += 1

        return chunks

    @staticmethod
    def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
        """Split text by sentences or characters with overlap."""
        if len(text) <= chunk_size:
            return [text]

        sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
        chunks: list[str] = []
        curr_chunk: list[str] = []
        curr_len = 0

        for s in sentences:
            s_fmt = s if s.endswith(".") else f"{s}."
            if curr_len + len(s_fmt) > chunk_size and curr_chunk:
                chunks.append(" ".join(curr_chunk))
                overlap_sentence = curr_chunk[-1] if curr_chunk else ""
                curr_chunk = [overlap_sentence, s_fmt] if overlap_sentence else [s_fmt]
                curr_len = sum(len(x) for x in curr_chunk)
            else:
                curr_chunk.append(s_fmt)
                curr_len += len(s_fmt)

        if curr_chunk:
            chunks.append(" ".join(curr_chunk))

        return chunks or [text]
