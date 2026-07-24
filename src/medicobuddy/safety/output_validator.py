"""Output validator — deterministic post-generation safety check.

Scans the composed response to block any content that violates MedicoBuddy's
safety contract BEFORE it reaches the user. This is the last deterministic
gate before delivery.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class OutputViolation:
    """A single safety violation found in the output."""

    violation_id: str
    category: str
    matched_text: str
    rule_description: str


@dataclass
class OutputValidationResult:
    """Result of output validation."""

    is_safe: bool
    violations: list[OutputViolation] = field(default_factory=list)
    sanitized_text: str = ""


# ── Blocked drug / medication names (non-exhaustive, extensible) ──
BLOCKED_DRUG_PATTERNS: list[str] = [
    # Common OTC and prescription drugs
    r"\b(?:paracetamol|acetaminophen|ibuprofen|aspirin|naproxen|diclofenac)\b",
    r"\b(?:tylenol|advil|motrin|aleve|crocin|dolo|combiflam)\b",
    r"\b(?:amoxicillin|azithromycin|ciprofloxacin|metformin|omeprazole)\b",
    r"\b(?:antibiotic|antifungal|antiviral|steroid|corticosteroid)\b",
    r"\b(?:benzodiazepine|opioid|nsaid)\b",
    # Dosage patterns
    r"\b\d+\s*(?:mg|mcg|ml|gram|tablet|capsule|pill|dose)\w*\b",
    r"\b(?:take|consume|swallow|administer)\s+\d+\b",
    r"\b(?:twice|thrice|once)\s+(?:a|per)\s+day\b.*\b(?:mg|tablet|capsule|pill)\b",
    r"\b(?:morning|evening|night)\s+dose\b",
]

# ── Blocked Ayurvedic ingestible formulations ────────────────
BLOCKED_AYURVEDA_PATTERNS: list[str] = [
    r"\b(?:bhasma|rasayana|kashaya|churna|vati|gutika)\b",
    r"\b(?:lehya|avaleha|asava|arishta|kwath|parpati)\b",
    r"\b(?:guggulu|triphala|ashwagandha|brahmi|tulsi)\b.*\b(?:tablet|capsule|powder|dose|mg)\b",
    r"\b(?:supplement|essential\s+oil|tincture|extract)\b.*\b(?:take|consume|dose|drop)\b",
]

# ── Blocked surgical / invasive terms ────────────────────────
BLOCKED_PROCEDURE_PATTERNS: list[str] = [
    r"\b(?:surgery|operat\w+|incision|resect\w+|excis\w+)\b",
    r"\b(?:induced?\s+vomit\w+|purg\w+|enema|colonic|detox\s+program)\b",
    r"\b(?:panchakarma|virechana|vamana|basti|nasya|raktamokshan)\b",
]

# ── Blocked unsafe claims ────────────────────────────────────
BLOCKED_CLAIM_PATTERNS: list[str] = [
    r"\byou\s+have\b",  # "you have [disease]" = diagnosis
    r"\bthis\s+will\s+cure\b",
    r"\bdefinitely\s+safe\b",
    r"\bno\s+need\s+to\s+(?:see|visit|consult)\s+a?\s*doctor\b",
    r"\bguarantee\w*\s+(?:recov|cur|heal)\w*\b",
    r"\b(?:proven|guaranteed)\s+(?:cure|remedy|treatment)\b",
]

# Pre-compile all blocked patterns
_ALL_BLOCKED: list[tuple[str, str, re.Pattern[str]]] = []
for _p in BLOCKED_DRUG_PATTERNS:
    _ALL_BLOCKED.append(("DRUG", "Drug or medication reference", re.compile(_p, re.IGNORECASE)))
for _p in BLOCKED_AYURVEDA_PATTERNS:
    _ALL_BLOCKED.append(("AYURVEDA_INGESTIBLE", "Ayurvedic ingestible formulation", re.compile(_p, re.IGNORECASE)))
for _p in BLOCKED_PROCEDURE_PATTERNS:
    _ALL_BLOCKED.append(("PROCEDURE", "Surgical or invasive procedure", re.compile(_p, re.IGNORECASE)))
for _p in BLOCKED_CLAIM_PATTERNS:
    _ALL_BLOCKED.append(("UNSAFE_CLAIM", "Unsafe or diagnostic claim", re.compile(_p, re.IGNORECASE)))


def validate_output(text: str) -> OutputValidationResult:
    """Scan composed response text for safety violations.

    Args:
        text: The response text to validate.

    Returns:
        OutputValidationResult with violations list and safety status.
    """
    violations: list[OutputViolation] = []
    violation_count = 0

    for category, description, pattern in _ALL_BLOCKED:
        matches = pattern.findall(text)
        for match in matches:
            violation_count += 1
            violations.append(
                OutputViolation(
                    violation_id=f"OV{violation_count:03d}",
                    category=category,
                    matched_text=match if isinstance(match, str) else str(match),
                    rule_description=description,
                )
            )

    return OutputValidationResult(
        is_safe=len(violations) == 0,
        violations=violations,
        sanitized_text=text if not violations else "",
    )


def check_provenance(response_text: str, citation_urls: list[str]) -> list[str]:
    """Verify that claims in the response have supporting citations.

    Simple heuristic: checks that the response contains citation markers
    and that citation URLs are non-empty.

    Args:
        response_text: The composed response.
        citation_urls: List of citation URLs provided.

    Returns:
        List of warning messages for unsupported claims.
    """
    warnings: list[str] = []

    # Check for factual claims without citation markers
    factual_patterns = re.compile(
        r"\b(?:studies?\s+show|research\s+(?:suggests?|indicates?)|"
        r"evidence\s+suggests?|according\s+to|data\s+shows?)\b",
        re.IGNORECASE,
    )

    factual_matches = factual_patterns.findall(response_text)
    if factual_matches and not citation_urls:
        warnings.append(
            "Response contains factual claims but no citations are provided."
        )

    # Check citation markers exist (e.g. [1], [2])
    citation_markers = re.findall(r"\[(\d+)\]", response_text)
    if citation_markers:
        max_cited = max(int(m) for m in citation_markers)
        if max_cited > len(citation_urls):
            warnings.append(
                f"Response references citation [{max_cited}] but only "
                f"{len(citation_urls)} citations are provided."
            )

    return warnings
