"""Graph traversal queries for knowledge graph retrieval with synonym expansion."""

from __future__ import annotations

from typing import Any

from medicobuddy.knowledge_graph.client import Neo4jClient


class KnowledgeGraphQueries:
    """Domain-specific Cypher queries for MedicoBuddy's knowledge graph.

    All symptom queries use fuzzy matching via CONTAINS for synonym coverage.
    """

    def __init__(self, client: Neo4jClient) -> None:
        self._client = client

    async def get_safe_actions_for_symptom(
        self, symptom_name: str
    ) -> list[dict[str, Any]]:
        """Retrieve self-care actions linked to a normalized symptom."""
        query = """
        MATCH (s:Symptom)
        WHERE toLower(s.name) CONTAINS toLower($symptom_name) OR toLower($symptom_name) CONTAINS toLower(s.name)
        MATCH (a:SelfCareAction)-[:ACTION_MAY_SUPPORT_SYMPTOM|MAY_HELP_WITH|MAY_SUPPORT]->(s)
        OPTIONAL MATCH (a)-[:ACTION_CONTRAINDICATED_FOR]->(ci:Contraindication)
        RETURN a.action_id AS action_id,
               a.action_name AS action_name,
               a.name AS name,
               a.description AS description,
               a.category AS category,
               a.risk_level AS risk_level,
               a.evidence_level AS evidence_level,
               collect(DISTINCT ci.description) AS contraindications
        ORDER BY a.action_name
        """
        return await self._client.execute_read(query, {"symptom_name": symptom_name})

    async def get_evidence_trail(self, symptom_name: str) -> list[dict[str, Any]]:
        """Traverse grounded evidence chain for Evidence Trail drawer.

        Traversal: symptom -> self-care action -> supporting passage -> source document
        """
        query = """
        MATCH (s:Symptom)
        WHERE toLower(s.name) CONTAINS toLower($symptom_name) OR toLower($symptom_name) CONTAINS toLower(s.name)
        OPTIONAL MATCH (a:SelfCareAction)-[:MAY_HELP_WITH|ACTION_MAY_SUPPORT_SYMPTOM|MAY_SUPPORT]->(s)
        OPTIONAL MATCH (a)-[:SUPPORTED_BY]->(pas:Passage)
        OPTIONAL MATCH (pas)-[:EXTRACTED_FROM]->(src:SourceDocument)
        RETURN s.name AS symptom,
               a.action_name AS self_care_action,
               a.description AS action_description,
               pas.passage_id AS chunk_id,
               pas.text AS passage_text,
               pas.section_title AS section_title,
               pas.page_number AS page_number,
               src.source_file AS source_file,
               src.title AS title,
               src.publisher AS publisher,
               src.url AS url
        LIMIT 20
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

    async def get_evidence_paths_for_entities(
        self, entities: list[str]
    ) -> list[dict[str, Any]]:
        """Traverse evidence paths for multiple entities (symptom, remedy, population, etc.)."""
        all_paths: list[dict[str, Any]] = []
        for entity in entities:
            # Try as symptom
            paths = await self.get_evidence_trail(entity)
            all_paths.extend(paths)
            # Try as remedy
            remedy_query = """
            MATCH (r:Remedy)
            WHERE toLower(r.name) CONTAINS toLower($entity)
            OPTIONAL MATCH (r)-[:REMEDY_FOR_SYMPTOM]->(s:Symptom)
            RETURN r.name AS remedy, s.name AS symptom, r.description AS description
            """
            remedy_paths = await self._client.execute_read(remedy_query, {"entity": entity})
            all_paths.extend(remedy_paths)
        return all_paths

    async def get_graph_counts(self) -> tuple[int, int]:
        """Return total node and relationship counts in graph."""
        return await self._client.get_graph_counts()

    async def smoke_test(self) -> dict[str, Any]:
        """Run a smoke test query against the graph."""
        try:
            nodes, rels = await self.get_graph_counts()
            # Test a simple traversal
            test_results = await self._client.execute_read(
                "MATCH (s:Symptom) RETURN s.name AS name LIMIT 3"
            )
            return {
                "ok": nodes > 0 and rels > 0,
                "nodes": nodes,
                "relationships": rels,
                "sample_symptoms": [r.get("name", "") for r in test_results],
            }
        except Exception as exc:
            return {"ok": False, "nodes": 0, "relationships": 0, "error": str(exc)}
