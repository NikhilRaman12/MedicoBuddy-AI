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
        """Retrieve self-care actions linked to a symptom with evidence levels."""
        query = """
        MATCH (s:Symptom)-[:ACTION_MAY_SUPPORT_SYMPTOM]-(a:SelfCareAction)
        WHERE toLower(s.name) CONTAINS toLower($symptom_name)
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

    async def get_red_flags_for_symptom(
        self, symptom_name: str
    ) -> list[dict[str, Any]]:
        """Retrieve red flags associated with a symptom."""
        query = """
        MATCH (s:Symptom)-[:SYMPTOM_HAS_RED_FLAG]->(rf:RedFlag)
        WHERE toLower(s.name) CONTAINS toLower($symptom_name)
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

    async def get_evidence_for_action(
        self, action_id: str
    ) -> list[dict[str, Any]]:
        """Retrieve evidence claims supporting a self-care action."""
        query = """
        MATCH (a:SelfCareAction {action_id: $action_id})
        OPTIONAL MATCH (ec:EvidenceClaim)-[:CLAIM_SUPPORTED_BY]->(st:Study)
        WHERE (ec)-[:EVIDENCE_FOR]->(a) OR (st)-[:STUDY_INVESTIGATES]->(a)
        RETURN ec.claim_id AS claim_id,
               ec.claim_text AS claim_text,
               ec.evidence_level AS evidence_level,
               ec.confidence AS confidence,
               st.study_id AS study_id,
               st.title AS study_title,
               st.study_design AS study_design,
               st.publication_date AS publication_date,
               st.retraction_status AS retraction_status
        """
        return await self._client.execute_read(query, {"action_id": action_id})

    async def get_ayurvedic_concepts_for_symptom(
        self, symptom_name: str
    ) -> list[dict[str, Any]]:
        """Retrieve Ayurvedic lifestyle concepts relevant to a symptom."""
        query = """
        MATCH (s:Symptom)<-[:ACTION_MAY_SUPPORT_SYMPTOM]-(a:SelfCareAction)
        WHERE toLower(s.name) CONTAINS toLower($symptom_name)
        OPTIONAL MATCH (ac:AyurvedicConcept)-[:CONCEPT_LINKED_TO_PRACTICE]->(lp:LifestylePractice)
        WHERE lp.name = a.name OR ac.name CONTAINS a.category
        RETURN ac.concept_id AS concept_id,
               ac.name AS concept_name,
               ac.description AS description,
               ac.evidence_category AS evidence_category,
               lp.name AS linked_practice
        """
        return await self._client.execute_read(query, {"symptom_name": symptom_name})

    async def check_ingredient_safety(
        self, ingredient_name: str, conditions: list[str]
    ) -> list[dict[str, Any]]:
        """Check if an ingredient has risks for given conditions."""
        query = """
        MATCH (i:Ingredient)-[:INGREDIENT_HAS_RISK]->(ae:AdverseEffect)
        WHERE toLower(i.name) CONTAINS toLower($ingredient_name)
        OPTIONAL MATCH (i)-[:INGREDIENT_INTERACTS_WITH]->(ix:Interaction)
        RETURN i.name AS ingredient,
               ae.name AS adverse_effect,
               ae.severity AS effect_severity,
               ix.description AS interaction_description
        """
        return await self._client.execute_read(
            query, {"ingredient_name": ingredient_name}
        )

    async def get_full_evidence_chain(
        self, claim_id: str
    ) -> list[dict[str, Any]]:
        """Traverse the full evidence chain: claim → study → source → org."""
        query = """
        MATCH (ec:EvidenceClaim {claim_id: $claim_id})
        OPTIONAL MATCH (ec)-[:CLAIM_SUPPORTED_BY]->(st:Study)
        OPTIONAL MATCH (ec)-[:CLAIM_CONTRADICTED_BY]->(contra_st:Study)
        OPTIONAL MATCH (st)<-[:SOURCE_PUBLISHED_BY]-(src:Source)
        OPTIONAL MATCH (src)-[:SOURCE_PUBLISHED_BY]->(org:Organization)
        RETURN ec.claim_text AS claim,
               ec.evidence_level AS evidence_level,
               ec.limitations AS limitations,
               collect(DISTINCT {
                   study_id: st.study_id,
                   title: st.title,
                   design: st.study_design,
                   retraction: st.retraction_status
               }) AS supporting_studies,
               collect(DISTINCT {
                   study_id: contra_st.study_id,
                   title: contra_st.title
               }) AS contradicting_studies,
               collect(DISTINCT {
                   source: src.title,
                   tier: src.tier,
                   url: src.url,
                   org: org.name
               }) AS sources
        """
        return await self._client.execute_read(query, {"claim_id": claim_id})
