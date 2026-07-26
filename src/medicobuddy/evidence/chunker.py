"""Semantic document chunking and metadata provenance generation with quarantine filters."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from medicobuddy.evidence.parser import ParsedDocument
from medicobuddy.safety.prompt_injection import check_retrieved_document

logger = logging.getLogger(__name__)

# Max chunk size in characters
DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 100

PROHIBITED_TERMS = {
    "cure for cancer",
    "ingest essential oil",
    "pure essential oil orally",
    "stop medical treatment",
    "do not consult a doctor",
    "rx prescription without doctor",
}


@dataclass
class EvidenceChunk:
    """Standardised evidence chunk with complete provenance metadata."""

    chunk_id: str
    doc_id: str
    text: str
    section_title: str
    page_number: int | None
    paragraph_number: int | None
    source_url: str
    publisher: str
    authors: list[str]
    publication_date: str
    retrieval_date: str
    licence: str
    language: str
    document_type: str
    study_type: str
    population: str
    evidence_tier: int
    retraction_status: str
    checksum: str
    quarantined: bool = False
    quarantine_reason: str = ""

    def to_metadata(self) -> dict[str, Any]:
        """Convert chunk into vector store metadata dictionary."""
        d = asdict(self)
        d["authors"] = ", ".join(self.authors) if isinstance(self.authors, list) else str(self.authors)
        return d


class DocumentChunker:
    """Chunks documents and evaluates quarantine criteria."""

    @staticmethod
    def chunk_document(
        doc: ParsedDocument,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> list[EvidenceChunk]:
        """Convert a ParsedDocument into a list of EvidenceChunks."""
        chunks: list[EvidenceChunk] = []
        chunk_idx = 1

        # Evaluate document-level quarantine
        if doc.retraction_status == "retracted":
            logger.warning("Document %s is retracted — quarantining", doc.doc_id)
            return [
                EvidenceChunk(
                    chunk_id=f"CHK_{doc.checksum[:8]}_1",
                    doc_id=doc.doc_id,
                    text=f"Retracted Document: {doc.title}",
                    section_title="Retracted",
                    page_number=None,
                    paragraph_number=None,
                    source_url=doc.url,
                    publisher=doc.publisher,
                    authors=doc.authors,
                    publication_date=doc.publication_date,
                    retrieval_date=doc.retrieval_date,
                    licence=doc.licence,
                    language=doc.language,
                    document_type=doc.document_type,
                    study_type=doc.study_type,
                    population=doc.population,
                    evidence_tier=doc.evidence_tier,
                    retraction_status="retracted",
                    checksum=doc.checksum,
                    quarantined=True,
                    quarantine_reason="Retracted document",
                )
            ]

        for sec in doc.sections:
            sec_text = sec.content.strip()
            if not sec_text:
                continue

            # Split section into chunks if longer than chunk_size
            sub_passages = DocumentChunker._split_text(sec_text, chunk_size, chunk_overlap)
            for passage in sub_passages:
                chunk_id = f"CHK_{doc.checksum[:8]}_{chunk_idx}"
                quarantined = False
                quarantine_reason = ""

                # Safety & injection check
                injection_check = check_retrieved_document(passage)
                if not injection_check.is_safe:
                    quarantined = True
                    quarantine_reason = f"Prompt injection detected: {injection_check.detected_patterns}"

                # Prohibited claims check
                passage_lower = passage.lower()
                for term in PROHIBITED_TERMS:
                    if term in passage_lower:
                        quarantined = True
                        quarantine_reason = f"Prohibited clinical claim detected: {term}"
                        break

                chunks.append(
                    EvidenceChunk(
                        chunk_id=chunk_id,
                        doc_id=doc.doc_id,
                        text=passage,
                        section_title=sec.section_title,
                        page_number=sec.page_number,
                        paragraph_number=sec.paragraph_number,
                        source_url=doc.url,
                        publisher=doc.publisher,
                        authors=doc.authors,
                        publication_date=doc.publication_date,
                        retrieval_date=doc.retrieval_date,
                        licence=doc.licence,
                        language=doc.language,
                        document_type=doc.document_type,
                        study_type=doc.study_type,
                        population=doc.population,
                        evidence_tier=doc.evidence_tier,
                        retraction_status=doc.retraction_status,
                        checksum=doc.checksum,
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
                # retain last sentence for overlap
                overlap_sentence = curr_chunk[-1] if curr_chunk else ""
                curr_chunk = [overlap_sentence, s_fmt] if overlap_sentence else [s_fmt]
                curr_len = sum(len(x) for x in curr_chunk)
            else:
                curr_chunk.append(s_fmt)
                curr_len += len(s_fmt)

        if curr_chunk:
            chunks.append(" ".join(curr_chunk))

        return chunks or [text]
