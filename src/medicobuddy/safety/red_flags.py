"""Deterministic red-flag triage engine.

This module uses ONLY pattern matching and rule-based logic — no LLM calls.
It runs twice: once before retrieval (on raw input) and once before final
response delivery (on composed output) to ensure no red-flag case slips through.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from medicobuddy.models.symptom import RedFlagMatch, TriageOutcome, TriageResult

if TYPE_CHECKING:
    from medicobuddy.models.user_context import UserContext


@dataclass(frozen=True)
class RedFlagRule:
    """A single deterministic red-flag detection rule."""

    flag_id: str
    flag_name: str
    patterns: list[str]  # regex patterns (case-insensitive)
    severity: str = "urgent"
    recommended_action: str = "Seek immediate emergency medical evaluation"
    requires_context: bool = False  # True if rule needs UserContext


# ────────────────────────────────────────────────────────────────
# Red-flag rule definitions — exhaustive, deterministic
# ────────────────────────────────────────────────────────────────

RED_FLAG_RULES: list[RedFlagRule] = [
    # ── Cardiac / Respiratory ────────────────────────────────
    RedFlagRule(
        flag_id="RF001",
        flag_name="Chest pain",
        patterns=[
            r"\bchest\s+pain\b", r"\bchest\s+tight\w*\b", r"\bchest\s+pressure\b",
            r"\bchest\s+squeeze\b", r"\bchest\s+crush\b", r"\bheart\s+attack\b",
            r"\bangina\b", r"\bcardiac\b",
        ],
    ),
    RedFlagRule(
        flag_id="RF002",
        flag_name="Breathing difficulty",
        patterns=[
            r"\bbreathing\s+difficult\w*\b", r"\bshortness\s+of\s+breath\b",
            r"\bcan'?t\s+breathe\b", r"\bcannot\s+breathe\b", r"\bsuffocating\b",
            r"\bchok(?:e|ing)\b", r"\bsevere\s+wheez\w*\b", r"\brespiratory\s+distress\b",
            r"\bdyspn[oe]a\b",
        ],
    ),
    RedFlagRule(
        flag_id="RF003",
        flag_name="Fainting or loss of consciousness",
        patterns=[
            r"\bfaint\w*\b", r"\bpassed?\s+out\b", r"\bloss\s+of\s+consciousness\b",
            r"\bunconscious\b", r"\bblack\w*\s*out\b", r"\bsyncope\b",
            r"\bcollaps\w*\b",
        ],
    ),
    RedFlagRule(
        flag_id="RF004",
        flag_name="Seizure",
        patterns=[
            r"\bseizure\w*\b", r"\bconvuls\w*\b", r"\bepileptic\b",
            r"\bfit\b(?:\s+(?:shaking|jerking))?",
        ],
    ),
    RedFlagRule(
        flag_id="RF005",
        flag_name="Bluish skin (cyanosis)",
        patterns=[
            r"\bblue?\s+(?:lips?|skin|finger\w*|nail\w*|face)\b",
            r"\bbluish\b", r"\bcyanosis\b", r"\bcyanotic\b",
        ],
    ),

    # ── Neurological ─────────────────────────────────────────
    RedFlagRule(
        flag_id="RF006",
        flag_name="Stroke symptoms",
        patterns=[
            r"\bfacial?\s+droop\w*\b", r"\bface\s+droop\w*\b",
            r"\bspeech\s+difficult\w*\b", r"\bslurred?\s+speech\b",
            r"\bcan'?t\s+(?:speak|talk)\b", r"\bsudden\s+weak\w*\b",
            r"\bone\s+side\s+weak\b", r"\bstroke\b", r"\bparalys\w*\b",
            r"\bnumb\w*\s+(?:one|left|right)\s+side\b",
        ],
    ),
    RedFlagRule(
        flag_id="RF007",
        flag_name="Sudden vision change",
        patterns=[
            r"\bsudden\s+(?:vision|blind|sight)\b", r"\bvision\s+(?:loss|change)\b",
            r"\bdouble\s+vision\b", r"\bcan'?t\s+see\b", r"\bblurred?\s+vision\b",
        ],
    ),
    RedFlagRule(
        flag_id="RF008",
        flag_name="Thunderclap / worst-ever headache",
        patterns=[
            r"\bworst\s+(?:ever|headache)\b", r"\bthunderclap\b",
            r"\bsudden\s+(?:severe|extreme|worst)\s+headache\b",
            r"\bexplosive\s+headache\b",
        ],
    ),
    RedFlagRule(
        flag_id="RF009",
        flag_name="Headache following injury",
        patterns=[
            r"\bhead(?:ache)?\s+(?:after|following|from)\s+(?:injury|fall|hit|accident|trauma)\b",
            r"\bhit\s+(?:my|the)\s+head\b", r"\bhead\s+injury\b",
            r"\bconcussion\b", r"\bhead\s+trauma\b",
        ],
    ),
    RedFlagRule(
        flag_id="RF010",
        flag_name="Stiff neck with fever/headache",
        patterns=[
            r"\bstiff\s+neck\b", r"\bneck\s+stiffness\b",
            r"\bneck\s+(?:is|feels)\s+(?:very\s+)?stiff\b",
            r"\bmeningit\w*\b", r"\bneck\s+rigid\w*\b",
        ],
    ),
    RedFlagRule(
        flag_id="RF011",
        flag_name="Confusion or altered consciousness",
        patterns=[
            r"\bconfus\w*\b", r"\bdisorient\w*\b",
            r"\baltered\s+(?:consciousness|mental)\b",
            r"\bdeliri\w*\b", r"\bincoherent\b",
            r"\bnot\s+(?:making|respond)\w*\b",
        ],
    ),

    # ── Abdominal ────────────────────────────────────────────
    RedFlagRule(
        flag_id="RF012",
        flag_name="Severe or localized abdominal pain",
        patterns=[
            r"\bsevere\s+(?:abdominal|stomach|belly|tummy)\s+pain\b",
            r"\b(?:right|left)\s+(?:lower|upper)\s+(?:abdominal|stomach|belly)\s+pain\b",
            r"\bappendic\w*\b", r"\bruptured?\b.*\b(?:abdom\w*|organ)\b",
            r"\bintense\s+(?:abdominal|stomach)\b",
        ],
    ),
    RedFlagRule(
        flag_id="RF013",
        flag_name="Rapidly worsening abdominal pain",
        patterns=[
            r"\b(?:abdominal|stomach|belly)\s+pain\b.*\b(?:worsening|worse|increasing|spreading)\b",
            r"\b(?:worsening|worse|increasing)\b.*\b(?:abdominal|stomach|belly)\s+pain\b",
        ],
    ),

    # ── GI bleeding / dehydration ────────────────────────────
    RedFlagRule(
        flag_id="RF014",
        flag_name="Blood in vomit or stool",
        patterns=[
            r"\bblood\s+in\s+(?:vomit|stool|poop)\b",
            r"\bvomit\w*\s+blood\b", r"\bbloody\s+(?:stool|vomit|poop)\b",
            r"\bblack\s+(?:and\s+tarry|stool|poop|tarry)\b",
            r"\bstool\s+(?:is\s+)?(?:black|tarry|bloody)\b",
            r"\bmelena\b", r"\bhematemesis\b", r"\bcoffee\s+ground\s+vomit\b",
        ],
    ),
    RedFlagRule(
        flag_id="RF015",
        flag_name="Persistent vomiting / severe dehydration",
        patterns=[
            r"\bpersisten\w*\s+vomit\w*\b", r"\bcan'?t\s+(?:keep|hold)\s+(?:anything|fluid|water|food)\b",
            r"\bsevere\s+dehydrat\w*\b", r"\bno\s+urin\w*\b",
            r"\bvomit\w*\s+(?:all\s+day|continuously|non[\s-]?stop|for\s+\d+\s+hours)\b",
            r"\bunable\s+to\s+(?:drink|retain|keep\s+down)\b",
        ],
    ),

    # ── Fever ────────────────────────────────────────────────
    RedFlagRule(
        flag_id="RF016",
        flag_name="High or dangerous fever",
        patterns=[
            r"\bfever\b.*\b(?:10[3-9]|1[1-9]\d)\s*[°f]?\b",
            r"\bfever\b.*\b(?:39\.[5-9]|4[0-9](?:\.\d)?)\s*[°c]?\b",
            r"\b(?:39\.[5-9]|4[0-9](?:\.\d)?)\s*(?:°?c|celsius)\b",
            r"\b(?:10[3-9]|1[1-9]\d)\s*(?:°?f|fahrenheit)\b",
            r"\bvery\s+high\s+fever\b", r"\bdangerous\s+fever\b",
        ],
    ),
    RedFlagRule(
        flag_id="RF017",
        flag_name="Fever with rash / stiff neck / confusion",
        patterns=[
            r"\bfever\b.*\brash\b", r"\brash\b.*\bfever\b",
            r"\bfever\b.*\bstiff\s+neck\b", r"\bfever\b.*\bconfus\w*\b",
            r"\bfever\b.*\bbreathing\s+(?:difficult|trouble|problem)\b",
            r"\bfever\b.*\bsevere\s+weak\w*\b",
        ],
    ),

    # ── Pregnancy ────────────────────────────────────────────
    RedFlagRule(
        flag_id="RF018",
        flag_name="Pregnancy with concerning symptoms",
        patterns=[
            r"\bpregnant\b.*\b(?:pain|fever|vomit|dizz\w*|bleed\w*|cramp)\b",
            r"\b(?:pain|fever|vomit|dizz\w*|bleed\w*)\b.*\bpregnant\b",
            r"\bpregnancy\s+(?:pain|bleed|complic)\w*\b",
        ],
        requires_context=True,
    ),

    # ── Poisoning / Overdose / Trauma ────────────────────────
    RedFlagRule(
        flag_id="RF019",
        flag_name="Poisoning or overdose",
        patterns=[
            r"\bpoison\w*\b", r"\boverdos\w*\b",
            r"\bswallow\w*\s+(?:chemical|cleaner|poison|pill|too\s+many)\b",
            r"\btoo\s+many\s+(?:pill|tablet|medicine)\w*\b",
            r"\baccidental\s+ingestion\b",
        ],
    ),
    RedFlagRule(
        flag_id="RF020",
        flag_name="Trauma or serious injury",
        patterns=[
            r"\bsevere\s+(?:injury|trauma|wound|burn|cut)\b",
            r"\bbroken\s+bone\b", r"\bfracture\b",
            r"\bheavy\s+bleed\w*\b", r"\bsevere\s+bleed\w*\b",
            r"\bstab\w*\b", r"\bgunshot\b",
        ],
    ),
    RedFlagRule(
        flag_id="RF021",
        flag_name="Allergic reaction / anaphylaxis",
        patterns=[
            r"\bsevere\s+allerg\w*\b", r"\banaphyla\w*\b",
            r"\bswelling\s+(?:face|throat|tongue|lips)\b",
            r"\bthroat\s+(?:closing|swelling|tight)\b",
            r"\bcan'?t\s+swallow\b",
        ],
    ),

    # ── General severity / worsening ─────────────────────────
    RedFlagRule(
        flag_id="RF022",
        flag_name="Severe or rapidly worsening symptoms",
        patterns=[
            r"\bsevere\s+(?:pain|symptom|weakness)\b",
            r"\brapidly\s+(?:worsening|getting\s+worse)\b",
            r"\bgetting\s+(?:much|significantly|rapidly)\s+worse\b",
            r"\bunbearable\s+pain\b", r"\bexcruciating\b",
        ],
    ),
    RedFlagRule(
        flag_id="RF023",
        flag_name="Suicidal or self-harm ideation",
        patterns=[
            r"\bsuicid\w*\b", r"\bself[\s-]?harm\b",
            r"\bkill\s+(?:myself|me)\b", r"\bwant\s+to\s+die\b",
            r"\bend\s+(?:my|it\s+all)\b",
        ],
    ),
]

# Pre-compile all patterns for performance
_COMPILED_RULES: list[tuple[RedFlagRule, list[re.Pattern[str]]]] = [
    (rule, [re.compile(p, re.IGNORECASE) for p in rule.patterns])
    for rule in RED_FLAG_RULES
]


def detect_red_flags(
    text: str,
    user_context: UserContext | None = None,
) -> list[RedFlagMatch]:
    """Scan text for red-flag patterns using deterministic rules.

    Args:
        text: User input or composed response text to scan.
        user_context: Optional user context for context-dependent rules.

    Returns:
        List of matched red flags. Empty list means no red flags detected.
    """
    matches: list[RedFlagMatch] = []
    normalized = text.lower().strip()

    for rule, compiled_patterns in _COMPILED_RULES:
        # Skip context-dependent rules if context is pregnancy-specific
        # but user is not pregnant
        if rule.requires_context and user_context is not None:
            if "pregnant" in rule.flag_id.lower():
                from medicobuddy.models.user_context import PregnancyStatus
                if user_context.pregnancy_status not in {
                    PregnancyStatus.PREGNANT,
                    PregnancyStatus.BREASTFEEDING,
                    PregnancyStatus.UNKNOWN,
                }:
                    continue

        matched_terms: list[str] = []
        for pattern in compiled_patterns:
            found = pattern.findall(normalized)
            matched_terms.extend(found)

        if matched_terms:
            matches.append(
                RedFlagMatch(
                    flag_id=rule.flag_id,
                    flag_name=rule.flag_name,
                    matched_terms=list(set(matched_terms)),
                    severity=rule.severity,
                    recommended_action=rule.recommended_action,
                )
            )

    return matches


def run_triage(
    text: str,
    user_context: UserContext | None = None,
    region: str = "IN",
    emergency_contacts: dict[str, dict[str, str]] | None = None,
) -> TriageResult:
    """Run the full deterministic triage engine.

    This runs BEFORE retrieval and AGAIN before final response delivery.

    Args:
        text: Text to triage (user message or composed response).
        user_context: User's health context.
        region: ISO country code for emergency contact selection.
        emergency_contacts: Region-to-contact mapping.

    Returns:
        TriageResult with outcome, red flags, and emergency contact if needed.
    """
    red_flags = detect_red_flags(text, user_context)
    scope_issues: list[str] = []

    # ── Check population scope ───────────────────────────────
    if user_context is not None and not user_context.is_in_target_population():
        from medicobuddy.models.user_context import AgeRange, PregnancyStatus

        if user_context.age_range == AgeRange.UNDER_18:
            scope_issues.append(
                "MedicoBuddy is designed for adults aged 18–65. "
                "Please consult a paediatrician or your child's healthcare provider."
            )
        elif user_context.age_range == AgeRange.OVER_65:
            scope_issues.append(
                "For adults over 65, we recommend consulting your healthcare provider "
                "for personalised guidance."
            )
        if user_context.pregnancy_status in {
            PregnancyStatus.PREGNANT,
            PregnancyStatus.BREASTFEEDING,
        }:
            scope_issues.append(
                "During pregnancy or breastfeeding, please consult your "
                "obstetrician or healthcare provider for any health concerns."
            )
        if user_context.is_immunocompromised:
            scope_issues.append(
                "For immunocompromised individuals, even mild symptoms may "
                "require professional evaluation. Please consult your doctor."
            )
        if user_context.has_significant_chronic_conditions():
            scope_issues.append(
                "Given your health conditions, we recommend discussing any "
                "symptoms with your treating physician."
            )

    # ── Determine outcome ────────────────────────────────────
    emergency_contact = None
    if red_flags:
        outcome = TriageOutcome.URGENT_CARE
        if emergency_contacts and region in emergency_contacts:
            emergency_contact = emergency_contacts[region]
        reasoning = (
            f"Red flag(s) detected: {', '.join(rf.flag_name for rf in red_flags)}. "
            "Immediate professional evaluation recommended."
        )
    elif scope_issues:
        outcome = TriageOutcome.OUT_OF_SCOPE
        reasoning = "User is outside the target population for self-care guidance."
    else:
        outcome = TriageOutcome.SELF_CARE
        reasoning = "No red flags detected. User is within scope for self-care information."

    return TriageResult(
        outcome=outcome,
        red_flags_detected=red_flags,
        scope_issues=scope_issues,
        confidence=1.0,  # Deterministic — always confident
        reasoning=reasoning,
        emergency_contact=emergency_contact,
    )
