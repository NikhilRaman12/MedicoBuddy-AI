"""Scope validator — ensures queries and symptoms are within MedicoBuddy's scope."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ScopeCheckResult:
    """Result of a scope validation check."""

    in_scope: bool
    reason: str = ""
    redirect_message: str = ""


# ── Permitted symptom categories (mild, short-duration) ──────
PERMITTED_SYMPTOMS: set[str] = {
    "headache", "head pain", "mild headache",
    "tiredness", "tired", "fatigue", "weakness", "feeling weak",
    "nausea", "mild nausea", "feeling nauseous", "queasy",
    "stomach discomfort", "stomach ache", "upset stomach", "indigestion",
    "mild fever", "low grade fever", "slight fever", "low fever",
    "digestive discomfort", "bloating", "gas", "acidity",
    "body ache", "body pain", "mild body pain",
    "mild cold", "uncomplicated cold", "runny nose", "stuffy nose", "nasal congestion",
    "sinus congestion", "mild sinus congestion",
    "allergy", "mild allergy", "seasonal allergy",
    "sore throat", "scratchy throat", "mild sore throat",
    "mild cough", "dry cough",
    "sleep", "sleep hygiene", "hydration", "water intake",
    "hair care", "skin care", "body care", "hygiene",
}

# ── Out-of-scope request patterns ────────────────────────────
OUT_OF_SCOPE_PATTERNS: list[tuple[str, str]] = [
    # Drug / medication requests
    (
        r"\b(?:prescri\w+|medicat\w+|medicine|drug|tablet|pill|capsule|syrup|injection"
        r"|antibiotic|paracetamol|ibuprofen|aspirin|acetaminophen|tylenol|advil"
        r"|dose|dosage|mg\b|milligram)\b",
        "MedicoBuddy cannot recommend, prescribe, or provide information about "
        "specific medications, dosages, or drugs. Please consult a pharmacist or doctor."
    ),
    # Surgery / invasive procedures
    (
        r"\b(?:surgery|surgic\w+|operat\w+|procedure|biopsy|endoscopy|colonoscopy"
        r"|invasive|transplant)\b",
        "MedicoBuddy cannot provide guidance on surgical or invasive procedures. "
        "Please consult the appropriate medical specialist."
    ),
    # Ayurvedic formulations (oral, medicinal-dose)
    (
        r"\b(?:bhasma|rasayana|kashaya|churna|vati|gutika|lehya|avaleha"
        r"|asava|arishta|taila|ghrita|guggulu|kwath|parpati"
        r"|supplement|essential\s+oil|tincture)\b",
        "MedicoBuddy cannot recommend oral Ayurvedic formulations, supplements, "
        "essential oils, or medicinal-dose herbs. Please consult a qualified "
        "Ayurvedic practitioner or healthcare provider."
    ),
    # Panchakarma / detox
    (
        r"\b(?:panchakarma|detox\w*|purgat\w+|enema|basti|virechana|vamana"
        r"|nasya|raktamokshan|fast(?:ing)?|induced\s+vomit)\b",
        "MedicoBuddy cannot recommend detoxification procedures, panchakarma, "
        "fasting protocols, or purification therapies. These require professional supervision."
    ),
    # Diagnosis requests
    (
        r"\b(?:diagnos\w+|what\s+(?:disease|condition|illness)\s+do\s+i\s+have"
        r"|am\s+i\s+(?:sick|ill)|do\s+i\s+have|is\s+it\s+(?:cancer|serious))\b",
        "MedicoBuddy cannot diagnose medical conditions. For diagnosis, "
        "please consult a qualified healthcare professional."
    ),
]

_COMPILED_OUT_OF_SCOPE: list[tuple[re.Pattern[str], str]] = [
    (re.compile(pattern, re.IGNORECASE), message)
    for pattern, message in OUT_OF_SCOPE_PATTERNS
]


def validate_query_scope(text: str) -> ScopeCheckResult:
    """Check if a user's query is within MedicoBuddy's permitted scope.

    Args:
        text: The user's input message.

    Returns:
        ScopeCheckResult indicating whether the query is in-scope.
    """
    normalized = text.lower().strip()

    # Check for out-of-scope patterns
    for pattern, message in _COMPILED_OUT_OF_SCOPE:
        if pattern.search(normalized):
            return ScopeCheckResult(
                in_scope=False,
                reason="out_of_scope_request",
                redirect_message=message,
            )

    return ScopeCheckResult(in_scope=True)


def validate_symptom_scope(symptom: str) -> ScopeCheckResult:
    """Validate that a symptom falls within the mild/short-duration scope.

    Args:
        symptom: The reported symptom text.

    Returns:
        ScopeCheckResult — in_scope=True if symptom is within permitted range.
    """
    normalized = symptom.lower().strip()

    # Check against permitted symptoms (fuzzy substring match)
    for permitted in PERMITTED_SYMPTOMS:
        if permitted in normalized or normalized in permitted:
            return ScopeCheckResult(in_scope=True)

    # If not clearly in permitted list, still allow if mild-qualified
    mild_qualifiers = re.compile(r"\b(?:mild|slight|minor|little|gentle|light)\b", re.IGNORECASE)
    if mild_qualifiers.search(normalized):
        return ScopeCheckResult(in_scope=True)

    # Default: allow but note uncertainty (the LLM + triage will further filter)
    return ScopeCheckResult(
        in_scope=True,
        reason="symptom_not_explicitly_listed",
    )
