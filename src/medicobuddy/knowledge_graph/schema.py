"""Canonical Neo4j schema definitions for MedicoBuddy AI.

Ensures strict typing and uniform traversal paths.
Includes all node labels and relationship types for the complete evidence graph.
"""

from __future__ import annotations

# ── Node Labels ─────────────────────────────────────────────
LABEL_SOURCE_DOCUMENT = "SourceDocument"
LABEL_PASSAGE = "Passage"
LABEL_SELF_CARE_ACTION = "SelfCareAction"
LABEL_SYMPTOM = "Symptom"
LABEL_AYURVEDIC_CONCEPT = "AyurvedicConcept"
LABEL_CONDITION = "Condition"
LABEL_CONTRAINDICATION = "Contraindication"
LABEL_RED_FLAG = "RedFlag"
LABEL_LIFESTYLE_PRACTICE = "LifestylePractice"
LABEL_REMEDY = "Remedy"

# ── Relationship Types ──────────────────────────────────────
REL_EXTRACTED_FROM = "EXTRACTED_FROM"
REL_SUPPORTED_BY = "SUPPORTED_BY"
REL_MAY_SUPPORT = "MAY_SUPPORT"
REL_MAY_HELP_WITH = "MAY_HELP_WITH"
REL_ACTION_MAY_SUPPORT_SYMPTOM = "ACTION_MAY_SUPPORT_SYMPTOM"
REL_CONTRAINDICATED_FOR = "CONTRAINDICATED_FOR"
REL_ACTION_CONTRAINDICATED_FOR = "ACTION_CONTRAINDICATED_FOR"
REL_CONDITION_CONTRAINDICATES = "CONDITION_CONTRAINDICATES"
REL_HAS_SAFETY_WARNING = "HAS_SAFETY_WARNING"
REL_SYMPTOM_HAS_RED_FLAG = "SYMPTOM_HAS_RED_FLAG"
REL_CONCEPT_LINKED_TO_PRACTICE = "CONCEPT_LINKED_TO_PRACTICE"
REL_REMEDY_FOR_SYMPTOM = "REMEDY_FOR_SYMPTOM"
REL_HAS_PASSAGE = "HAS_PASSAGE"
REL_MAKES_CLAIM = "MAKES_CLAIM"


def get_constraint_statements() -> list[str]:
    """Return Cypher statements to create canonical constraints."""
    return [
        f"CREATE CONSTRAINT source_doc_id IF NOT EXISTS FOR (n:{LABEL_SOURCE_DOCUMENT}) REQUIRE n.source_file IS UNIQUE",
        f"CREATE CONSTRAINT passage_id IF NOT EXISTS FOR (n:{LABEL_PASSAGE}) REQUIRE n.passage_id IS UNIQUE",
        f"CREATE CONSTRAINT action_name IF NOT EXISTS FOR (n:{LABEL_SELF_CARE_ACTION}) REQUIRE n.action_name IS UNIQUE",
        f"CREATE CONSTRAINT symptom_name IF NOT EXISTS FOR (n:{LABEL_SYMPTOM}) REQUIRE n.name IS UNIQUE",
        f"CREATE CONSTRAINT condition_name IF NOT EXISTS FOR (n:{LABEL_CONDITION}) REQUIRE n.name IS UNIQUE",
        f"CREATE CONSTRAINT remedy_name IF NOT EXISTS FOR (n:{LABEL_REMEDY}) REQUIRE n.name IS UNIQUE",
    ]


def get_index_statements() -> list[str]:
    """Return Cypher statements to create useful indexes."""
    return [
        f"CREATE INDEX symptom_name_idx IF NOT EXISTS FOR (n:{LABEL_SYMPTOM}) ON (n.name)",
        f"CREATE INDEX action_category_idx IF NOT EXISTS FOR (n:{LABEL_SELF_CARE_ACTION}) ON (n.category)",
        f"CREATE INDEX passage_source_idx IF NOT EXISTS FOR (n:{LABEL_PASSAGE}) ON (n.source_file)",
    ]


def get_namespace_clear_statements() -> list[str]:
    """Return Cypher statements to clear only MedicoBuddy nodes."""
    return [
        f"MATCH (n:{LABEL_SOURCE_DOCUMENT}) DETACH DELETE n",
        f"MATCH (n:{LABEL_PASSAGE}) DETACH DELETE n",
        f"MATCH (n:{LABEL_SELF_CARE_ACTION}) DETACH DELETE n",
        f"MATCH (n:{LABEL_SYMPTOM}) DETACH DELETE n",
        f"MATCH (n:{LABEL_AYURVEDIC_CONCEPT}) DETACH DELETE n",
        f"MATCH (n:{LABEL_CONDITION}) DETACH DELETE n",
        f"MATCH (n:{LABEL_CONTRAINDICATION}) DETACH DELETE n",
        f"MATCH (n:{LABEL_RED_FLAG}) DETACH DELETE n",
        f"MATCH (n:{LABEL_LIFESTYLE_PRACTICE}) DETACH DELETE n",
        f"MATCH (n:{LABEL_REMEDY}) DETACH DELETE n",
    ]
