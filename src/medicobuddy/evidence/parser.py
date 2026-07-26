"""Document parsers for PDF, XML, HTML, JSON, and Plain Text with layout-aware section locators."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


@dataclass
class ParsedSection:
    """A section inside a document with title and content."""

    section_title: str
    content: str
    page_number: int | None = None
    paragraph_number: int | None = None


@dataclass
class ParsedDocument:
    """Normalized document representation."""

    doc_id: str
    title: str
    publisher: str
    authors: list[str]
    publication_date: str
    retrieval_date: str
    url: str
    licence: str
    language: str
    document_type: str
    study_type: str
    population: str
    evidence_tier: int
    retraction_status: str
    checksum: str
    sections: list[ParsedSection] = field(default_factory=list)
    raw_metadata: dict[str, Any] = field(default_factory=dict)


def compute_sha256(content: bytes | str) -> str:
    """Compute SHA-256 checksum of document content."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


class DocumentParser:
    """Parser for evidence documents in various formats."""

    @staticmethod
    def parse_file(
        file_path: Path | str,
        manifest_meta: dict[str, Any] | None = None,
    ) -> ParsedDocument:
        """Parse a local file based on its extension."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        raw_bytes = path.read_bytes()
        checksum = compute_sha256(raw_bytes)
        doc_id = f"DOC_{checksum[:12]}"

        meta = manifest_meta or {}
        doc_title = meta.get("title") or path.stem.replace("_", " ").title()
        publisher = meta.get("publisher") or "Unknown Publisher"
        licence = meta.get("licence") or "Open Access"
        url = meta.get("url") or f"file://{path.name}"
        evidence_tier = int(meta.get("evidence_tier", 1))

        sections: list[ParsedSection] = []
        ext = path.suffix.lower()

        if ext == ".pdf":
            sections = DocumentParser._parse_pdf(path)
        elif ext in {".xml", ".nlm"}:
            sections = DocumentParser._parse_xml(raw_bytes.decode("utf-8", errors="ignore"))
        elif ext in {".html", ".htm"}:
            sections = DocumentParser._parse_html(raw_bytes.decode("utf-8", errors="ignore"))
        elif ext == ".json":
            sections = DocumentParser._parse_json(raw_bytes.decode("utf-8", errors="ignore"))
        else:
            sections = DocumentParser._parse_text(raw_bytes.decode("utf-8", errors="ignore"))

        return ParsedDocument(
            doc_id=doc_id,
            title=doc_title,
            publisher=publisher,
            authors=meta.get("authors", []),
            publication_date=meta.get("last_updated") or "2026-01-01",
            retrieval_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            url=url,
            licence=licence,
            language=meta.get("language") or "en",
            document_type=meta.get("document_type") or "Guideline",
            study_type=meta.get("study_type") or "Systematic Review",
            population=meta.get("target_population") or "adults_18_65",
            evidence_tier=evidence_tier,
            retraction_status=meta.get("retraction_status") or "active",
            checksum=checksum,
            sections=sections,
            raw_metadata=meta,
        )

    @staticmethod
    def _parse_text(text: str) -> list[ParsedSection]:
        """Parse plain text into sections based on headers or double newlines."""
        sections: list[ParsedSection] = []
        lines = text.splitlines()
        current_title = "Overview"
        current_buf: list[str] = []

        para_num = 1
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#") or (len(stripped) < 60 and stripped.isupper()):
                if current_buf:
                    sections.append(
                        ParsedSection(
                            section_title=current_title,
                            content=" ".join(current_buf),
                            paragraph_number=para_num,
                        )
                    )
                    para_num += 1
                    current_buf = []
                current_title = stripped.lstrip("#").strip()
            else:
                current_buf.append(stripped)

        if current_buf:
            sections.append(
                ParsedSection(
                    section_title=current_title,
                    content=" ".join(current_buf),
                    paragraph_number=para_num,
                )
            )

        return sections or [ParsedSection(section_title="General", content=text)]

    @staticmethod
    def _parse_xml(xml_content: str) -> list[ParsedSection]:
        """Parse NLM/PubMed XML documents into structured sections."""
        sections: list[ParsedSection] = []
        try:
            root = ET.fromstring(xml_content)
            # MedlinePlus XML parsing
            for item in root.findall(".//document") + root.findall(".//nlmSearchResult/list/document"):
                title_elem = item.find("title") or item.find(".//*[@name='title']")
                title = title_elem.text if title_elem is not None and title_elem.text else "Health Topic"

                snippet_elem = item.find("snippet") or item.find(".//*[@name='snippet']")
                snippet = snippet_elem.text if snippet_elem is not None and snippet_elem.text else ""

                if snippet:
                    sections.append(ParsedSection(section_title=title, content=snippet))

            # Generic XML fallback if no NLM documents found
            if not sections:
                for elem in root.iter():
                    if elem.text and len(elem.text.strip()) > 30:
                        sections.append(
                            ParsedSection(
                                section_title=elem.tag.capitalize(),
                                content=elem.text.strip(),
                            )
                        )
        except Exception as exc:
            logger.warning("XML parsing failed — treating as plain text: %s", exc)
            return DocumentParser._parse_text(xml_content)

        return sections or [ParsedSection(section_title="XML Extract", content=xml_content[:1000])]

    @staticmethod
    def _parse_html(html_content: str) -> list[ParsedSection]:
        """Parse HTML content extracting headings and paragraph text."""
        # Simple regex-based HTML text extractor to avoid heavy dependencies if BS4 is absent
        clean_text = re.sub(r"<script.*?>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
        clean_text = re.sub(r"<style.*?>.*?</style>", "", clean_text, flags=re.DOTALL | re.IGNORECASE)
        clean_text = re.sub(r"<[^>]+>", "\n", clean_text)
        clean_text = re.sub(r"\n\s*\n", "\n\n", clean_text)
        return DocumentParser._parse_text(clean_text)

    @staticmethod
    def _parse_json(json_content: str) -> list[ParsedSection]:
        """Parse JSON document structure into sections."""
        sections: list[ParsedSection] = []
        try:
            data = json.loads(json_content)
            if isinstance(data, list):
                for i, item in enumerate(data, 1):
                    if isinstance(item, dict):
                        title = item.get("title") or item.get("topic") or f"Item {i}"
                        text = item.get("content") or item.get("text") or json.dumps(item)
                        sections.append(ParsedSection(section_title=title, content=str(text)))
            elif isinstance(data, dict):
                for key, val in data.items():
                    sections.append(ParsedSection(section_title=str(key), content=str(val)))
        except Exception:
            return DocumentParser._parse_text(json_content)

        return sections or [ParsedSection(section_title="JSON Data", content=json_content[:1000])]

    @staticmethod
    def _parse_pdf(pdf_path: Path) -> list[ParsedSection]:
        """Parse PDF document using pdfminer/pypdf if available, else text fallback."""
        sections: list[ParsedSection] = []
        try:
            import pypdf
            reader = pypdf.PdfReader(str(pdf_path))
            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text and text.strip():
                    sections.append(
                        ParsedSection(
                            section_title=f"Page {idx}",
                            content=text.strip(),
                            page_number=idx,
                        )
                    )
        except Exception:
            logger.warning("pypdf parsing failed for %s", pdf_path)
            sections.append(
                ParsedSection(
                    section_title="PDF Content",
                    content=f"Raw PDF File: {pdf_path.name}",
                )
            )

        return sections
