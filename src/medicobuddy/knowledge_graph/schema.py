"""Canonical Neo4j schema definitions for MedicoBuddy AI.

Ensures strict typing and uniform traversal paths.
"""

from __future__ import annotations

# Node Labels
LABEL_SOURCE_DOCUMENT = "SourceDocument"
LABEL_PASSAGE = "Passage"
LABEL_SELF_CARE_ACTION = "SelfCareAction"
LABEL_SYMPTOM = "Symptom"

# Relationship Types
REL_EXTRACTED_FROM = "EXTRACTED_FROM"
REL_SUPPORTED_BY = "SUPPORTED_BY"
REL_MAY_SUPPORT = "MAY_SUPPORT"
REL_CONTRAINDICATED_FOR = "CONTRAINDICATED_FOR"
REL_HAS_SAFETY_WARNING = "HAS_SAFETY_WARNING"


def get_constraint_statements() -> list[str]:
    """Return Cypher statements to create canonical constraints."""
    return [
        f"CREATE CONSTRAINT source_doc_id IF NOT EXISTS FOR (n:{LABEL_SOURCE_DOCUMENT}) REQUIRE n.source_file IS UNIQUE",
        f"CREATE CONSTRAINT passage_id IF NOT EXISTS FOR (n:{LABEL_PASSAGE}) REQUIRE n.passage_id IS UNIQUE",
        f"CREATE CONSTRAINT action_name IF NOT EXISTS FOR (n:{LABEL_SELF_CARE_ACTION}) REQUIRE n.action_name IS UNIQUE",
        f"CREATE CONSTRAINT symptom_name IF NOT EXISTS FOR (n:{LABEL_SYMPTOM}) REQUIRE n.name IS UNIQUE",
    ]


def get_namespace_clear_statements() -> list[str]:
    """Return Cypher statements to clear only MedicoBuddy nodes."""
    return [
        f"MATCH (n:{LABEL_SOURCE_DOCUMENT}) DETACH DELETE n",
        f"MATCH (n:{LABEL_PASSAGE}) DETACH DELETE n",
        f"MATCH (n:{LABEL_SELF_CARE_ACTION}) DETACH DELETE n",
        f"MATCH (n:{LABEL_SYMPTOM}) DETACH DELETE n",
    ]
