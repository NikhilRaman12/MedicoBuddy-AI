"""Graph traversal queries for knowledge graph retrieval."""

from __future__ import annotations

from typing import Any

from medicobuddy.knowledge_graph.client import Neo4jClient


class KnowledgeGraphQueries:
    """Domain-specific Cypher queries for MedicoBuddy's knowledge graph."""

    def __init__(self, client: Neo4jClient) -> None:
        self._client = client

    async def get_safe_actions_for_symptom(
        self, symptom_name: str
    ) -> list[dict[str, Any]]:
        """Retrieve self-care actions linked to a normalized symptom."""
        query = """
        MATCH (s:Symptom)
        WHERE toLower(s.name) CONTAINS toLower($symptom_name) OR toLower($symptom_name) CONTAINS toLower(s.name)
        MATCH (a:SelfCareAction)-[:ACTION_MAY_SUPPORT_SYMPTOM|MAY_HELP_WITH]->(s)
        OPTIONAL MATCH (a)-[:ACTION_CONTRAINDICATED_FOR]->(ci:Contraindication)
        RETURN a.action_id AS action_id,
               a.name AS action_name,
               a.description AS description,
               a.category AS category,
               a.risk_level AS risk_level,
               collect(DISTINCT ci.description) AS contraindications
        ORDER BY a.name
        """
        return await self._client.execute_read(query, {"symptom_name": symptom_name})

    async def get_evidence_trail(self, symptom_name: str) -> list[dict[str, Any]]:
        """Traverse grounded evidence chain for Evidence Trail drawer.

        Traversal: User concern -> normalized symptom -> eligible self-care action -> supporting claim -> passage -> source
        """
        query = """
        MATCH (s:Symptom)
        WHERE toLower(s.name) CONTAINS toLower($symptom_name) OR toLower($symptom_name) CONTAINS toLower(s.name)
        OPTIONAL MATCH (a:SelfCareAction)-[:MAY_HELP_WITH|ACTION_MAY_SUPPORT_SYMPTOM]->(s)
        OPTIONAL MATCH (c:Claim)-[:APPLIES_TO]->(s)
        OPTIONAL MATCH (pas:Passage)-[:MAKES_CLAIM]->(c)
        OPTIONAL MATCH (doc:Document)-[:HAS_PASSAGE]->(pas)
        OPTIONAL MATCH (src:Source)-[:HAS_DOCUMENT]->(doc)
        OPTIONAL MATCH (src)-[:PUBLISHED_BY]->(org:Organization)
        RETURN s.name AS symptom,
               a.name AS self_care_action,
               c.text AS claim,
               pas.text AS passage,
               src.name AS source_name,
               src.url AS source_url,
               org.name AS organization
        LIMIT 5
        """
        return await self._client.execute_read(query, {"symptom_name": symptom_name})

    async def get_red_flags_for_symptom(
        self, symptom_name: str
    ) -> list[dict[str, Any]]:
        """Retrieve red flags associated with a normalized symptom."""
        query = """
        MATCH (s:Symptom)
        WHERE toLower(s.name) CONTAINS toLower($symptom_name) OR toLower($symptom_name) CONTAINS toLower(s.name)
        MATCH (s)-[:SYMPTOM_HAS_RED_FLAG|HAS_RED_FLAG]->(rf:RedFlag)
        RETURN rf.flag_id AS flag_id,
               rf.name AS flag_name,
               rf.description AS description,
               rf.urgency AS urgency
        """
        return await self._client.execute_read(query, {"symptom_name": symptom_name})

    async def get_contraindications_for_condition(
        self, condition_name: str
    ) -> list[dict[str, Any]]:
        """Retrieve contraindications for a specific condition."""
        query = """
        MATCH (c:Condition)-[:CONDITION_CONTRAINDICATES]->(ci:Contraindication)
        WHERE toLower(c.name) CONTAINS toLower($condition_name)
        RETURN ci.contra_id AS contra_id,
               ci.description AS description,
               ci.applies_to AS applies_to
        """
        return await self._client.execute_read(query, {"condition_name": condition_name})

    async def get_ayurvedic_concepts_for_symptom(
        self, symptom_name: str
    ) -> list[dict[str, Any]]:
        """Retrieve Ayurvedic lifestyle concepts relevant to a symptom."""
        query = """
        MATCH (s:Symptom)
        WHERE toLower(s.name) CONTAINS toLower($symptom_name) OR toLower($symptom_name) CONTAINS toLower(s.name)
        OPTIONAL MATCH (ac:AyurvedicConcept)-[:CONCEPT_LINKED_TO_PRACTICE]->(lp:LifestylePractice)
        RETURN ac.concept_id AS concept_id,
               ac.name AS concept_name,
               ac.description AS description,
               ac.evidence_category AS evidence_category,
               lp.name AS linked_practice
        """
        return await self._client.execute_read(query, {"symptom_name": symptom_name})
