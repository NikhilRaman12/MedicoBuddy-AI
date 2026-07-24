"""User context model — collects only minimum-necessary information, no PII."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class AgeRange(StrEnum):
    """Age bracket — no exact age stored."""

    UNDER_18 = "under_18"
    AGE_18_25 = "18_25"
    AGE_26_35 = "26_35"
    AGE_36_45 = "36_45"
    AGE_46_55 = "46_55"
    AGE_56_65 = "56_65"
    OVER_65 = "over_65"
    UNKNOWN = "unknown"


class PregnancyStatus(StrEnum):
    """Pregnancy / breastfeeding status."""

    NOT_PREGNANT = "not_pregnant"
    PREGNANT = "pregnant"
    BREASTFEEDING = "breastfeeding"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class UserContext(BaseModel):
    """Minimum-necessary user health context for triage and guidance.

    Stores NO personally identifiable information (no name, address, ID).
    """

    age_range: AgeRange = AgeRange.UNKNOWN
    pregnancy_status: PregnancyStatus = PregnancyStatus.UNKNOWN
    is_immunocompromised: bool | None = None

    chronic_conditions: list[str] = Field(
        default_factory=list,
        description="Known chronic conditions (e.g. diabetes, hypertension, kidney disease)",
    )
    allergies: list[str] = Field(
        default_factory=list,
        description="Known food or environmental allergies",
    )
    intolerances: list[str] = Field(
        default_factory=list,
        description="Known food intolerances (e.g. lactose, gluten)",
    )
    current_medications: list[str] = Field(
        default_factory=list,
        description="Currently taking medications (names only, for interaction awareness)",
    )
    dietary_restrictions: list[str] = Field(
        default_factory=list,
        description="Dietary restrictions (e.g. diabetic diet, renal diet)",
    )
    region: str = Field(default="IN", description="ISO country code for emergency contacts")

    def is_in_target_population(self) -> bool:
        """Check if user falls within the target adult population (18-65)."""
        excluded_ages = {AgeRange.UNDER_18, AgeRange.OVER_65, AgeRange.UNKNOWN}
        if self.age_range in excluded_ages:
            return False
        if self.pregnancy_status in {PregnancyStatus.PREGNANT, PregnancyStatus.BREASTFEEDING}:
            return False
        if self.is_immunocompromised:
            return False
        return True

    def has_significant_chronic_conditions(self) -> bool:
        """Check for conditions requiring professional oversight."""
        significant = {
            "cancer", "hiv", "aids", "organ transplant", "dialysis",
            "chemotherapy", "radiation therapy", "autoimmune",
        }
        return any(
            any(s in condition.lower() for s in significant)
            for condition in self.chronic_conditions
        )
