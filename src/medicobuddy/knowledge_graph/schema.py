"""Neo4j knowledge graph schema — node types, relationships, and constraints."""

from __future__ import annotations

# ────────────────────────────────────────────────────────────────
# Schema creation Cypher statements
# Run these once during database initialisation.
# ────────────────────────────────────────────────────────────────

SCHEMA_CONSTRAINTS: list[str] = [
    # Unique constraints on primary keys
    "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Symptom) REQUIRE s.symptom_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (r:RedFlag) REQUIRE r.flag_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (a:SelfCareAction) REQUIRE a.action_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (ac:AyurvedicConcept) REQUIRE ac.concept_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (lp:LifestylePractice) REQUIRE lp.practice_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (ci:Contraindication) REQUIRE ci.contra_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (pg:PopulationGroup) REQUIRE pg.group_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Condition) REQUIRE c.condition_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (ec:EvidenceClaim) REQUIRE ec.claim_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (st:Study) REQUIRE st.study_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (g:Guideline) REQUIRE g.guideline_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Organization) REQUIRE o.org_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Ingredient) REQUIRE i.ingredient_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (ae:AdverseEffect) REQUIRE ae.effect_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (ix:Interaction) REQUIRE ix.interaction_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (src:Source) REQUIRE src.source_id IS UNIQUE",
]

SCHEMA_INDEXES: list[str] = [
    "CREATE INDEX IF NOT EXISTS FOR (s:Symptom) ON (s.name)",
    "CREATE INDEX IF NOT EXISTS FOR (r:RedFlag) ON (r.name)",
    "CREATE INDEX IF NOT EXISTS FOR (a:SelfCareAction) ON (a.name)",
    "CREATE INDEX IF NOT EXISTS FOR (ec:EvidenceClaim) ON (ec.evidence_level)",
    "CREATE INDEX IF NOT EXISTS FOR (st:Study) ON (st.study_design)",
    "CREATE INDEX IF NOT EXISTS FOR (st:Study) ON (st.publication_date)",
    "CREATE INDEX IF NOT EXISTS FOR (src:Source) ON (src.tier)",
]

# ────────────────────────────────────────────────────────────────
# Node property definitions (documentation)
# ────────────────────────────────────────────────────────────────

NODE_DEFINITIONS: dict[str, dict[str, str]] = {
    "Symptom": {
        "symptom_id": "Unique identifier",
        "name": "Symptom name (e.g. 'mild headache')",
        "description": "Plain-language description",
        "body_location": "Body area affected",
        "severity_range": "Expected severity range (mild/moderate)",
    },
    "RedFlag": {
        "flag_id": "Matches red_flags.py rule IDs (e.g. RF001)",
        "name": "Red flag name",
        "description": "Why this is a red flag",
        "urgency": "urgent / emergency",
    },
    "SelfCareAction": {
        "action_id": "Unique identifier",
        "name": "Action name (e.g. 'rest', 'hydration')",
        "description": "Detailed guidance",
        "category": "rest / hydration / positioning / breathing / diet / environment",
        "risk_level": "low / minimal",
    },
    "AyurvedicConcept": {
        "concept_id": "Unique identifier",
        "name": "Concept name (e.g. 'warm water intake')",
        "description": "Non-pharmacological lifestyle concept",
        "evidence_category": "evidence_supported / limited_preliminary / traditional_insufficient / evidence_of_risk / conflicting",
        "source_tradition": "Text or tradition of origin",
    },
    "LifestylePractice": {
        "practice_id": "Unique identifier",
        "name": "Practice name",
        "description": "Description of the lifestyle practice",
        "category": "breathing / movement / sleep / routine",
    },
    "Contraindication": {
        "contra_id": "Unique identifier",
        "description": "What is contraindicated and why",
        "applies_to": "Condition or population group",
    },
    "PopulationGroup": {
        "group_id": "Unique identifier",
        "name": "Group name (e.g. 'pregnant', 'diabetic', 'child')",
        "age_range": "Age bracket if applicable",
        "in_scope": "Whether MedicoBuddy serves this group (boolean)",
    },
    "Condition": {
        "condition_id": "Unique identifier",
        "name": "Condition name (e.g. 'diabetes', 'hypertension')",
        "relevance": "Why this condition matters for self-care scope",
    },
    "EvidenceClaim": {
        "claim_id": "Unique identifier",
        "claim_text": "The factual claim",
        "evidence_level": "high / moderate / limited / insufficient",
        "confidence": "0.0–1.0 score",
        "date_assessed": "When last reviewed",
        "limitations": "Known limitations",
        "provenance": "Source chain summary",
    },
    "Study": {
        "study_id": "PMID, DOI, or internal ID",
        "title": "Study title",
        "authors": "Author list",
        "publication_date": "Date published",
        "study_design": "RCT, cohort, meta-analysis, etc.",
        "sample_size": "Number of participants",
        "retraction_status": "none / retracted / corrected",
    },
    "Guideline": {
        "guideline_id": "Unique identifier",
        "title": "Guideline title",
        "issuing_body": "Organization that issued it",
        "publication_date": "Date",
        "url": "Canonical URL",
    },
    "Organization": {
        "org_id": "Unique identifier",
        "name": "Organization name (e.g. 'WHO', 'AYUSH')",
        "type": "government / professional_body / research_institution",
    },
    "Ingredient": {
        "ingredient_id": "Unique identifier",
        "name": "Ingredient name",
        "category": "food / spice / herb",
        "common_use": "Culinary, beverage, etc.",
    },
    "AdverseEffect": {
        "effect_id": "Unique identifier",
        "name": "Effect name",
        "severity": "mild / moderate / severe",
    },
    "Interaction": {
        "interaction_id": "Unique identifier",
        "description": "Description of the interaction",
        "severity": "mild / moderate / severe",
    },
    "Source": {
        "source_id": "DOI, URL, or internal ID",
        "title": "Source title",
        "tier": "1–7 per evidence hierarchy",
        "url": "Canonical URL",
        "publication_date": "Date",
        "type": "journal / guideline / database / blog",
    },
}

# ────────────────────────────────────────────────────────────────
# Relationship definitions
# ────────────────────────────────────────────────────────────────

RELATIONSHIP_DEFINITIONS: dict[str, dict[str, str]] = {
    "SYMPTOM_HAS_RED_FLAG": {
        "from": "Symptom",
        "to": "RedFlag",
        "description": "Symptom pattern that constitutes a red flag",
    },
    "ACTION_MAY_SUPPORT_SYMPTOM": {
        "from": "SelfCareAction",
        "to": "Symptom",
        "properties": "evidence_level, confidence, conditions",
    },
    "ACTION_CONTRAINDICATED_FOR": {
        "from": "SelfCareAction",
        "to": "Contraindication",
        "description": "Action is unsafe for certain conditions",
    },
    "CLAIM_SUPPORTED_BY": {
        "from": "EvidenceClaim",
        "to": "Study",
        "properties": "relevance_score",
    },
    "CLAIM_CONTRADICTED_BY": {
        "from": "EvidenceClaim",
        "to": "Study",
        "properties": "contradiction_type",
    },
    "STUDY_INVESTIGATES": {
        "from": "Study",
        "to": "Symptom | SelfCareAction | AyurvedicConcept",
    },
    "SOURCE_PUBLISHED_BY": {
        "from": "Source",
        "to": "Organization",
    },
    "INGREDIENT_HAS_RISK": {
        "from": "Ingredient",
        "to": "AdverseEffect",
        "properties": "population_group, conditions",
    },
    "PRACTICE_REQUIRES_PROFESSIONAL": {
        "from": "LifestylePractice",
        "to": "PopulationGroup",
        "description": "Practice needs professional guidance for this group",
    },
    "EVIDENCE_APPLIES_TO_POPULATION": {
        "from": "EvidenceClaim",
        "to": "PopulationGroup",
    },
    "CONCEPT_LINKED_TO_PRACTICE": {
        "from": "AyurvedicConcept",
        "to": "LifestylePractice",
    },
    "CONDITION_CONTRAINDICATES": {
        "from": "Condition",
        "to": "Contraindication",
    },
    "INGREDIENT_INTERACTS_WITH": {
        "from": "Ingredient",
        "to": "Interaction",
    },
}
