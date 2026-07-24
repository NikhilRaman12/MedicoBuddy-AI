"""ClinicalTrials.gov API v2 MCP connector."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from medicobuddy.mcp.base import MCPConnector
from medicobuddy.models.mcp import MCPResult

logger = logging.getLogger(__name__)

CT_API_BASE = "https://clinicaltrials.gov/api/v2"


class ClinicalTrialsConnector(MCPConnector):
    """Read-only connector for ClinicalTrials.gov API v2."""

    connector_name = "clinicaltrials_gov"

    async def is_available(self) -> bool:
        try:
            await self._get(f"{CT_API_BASE}/version")
            return True
        except Exception:
            logger.warning("ClinicalTrials.gov connector unavailable")
            return False

    async def search(self, query: str, max_results: int = 5) -> list[MCPResult]:
        """Search ClinicalTrials.gov for relevant trials."""
        params = {
            "query.term": query,
            "pageSize": str(min(max_results, 20)),
            "format": "json",
            "fields": (
                "NCTId,BriefTitle,OverallStatus,Phase,StartDate,"
                "CompletionDate,EnrollmentCount,Condition,InterventionName,"
                "BriefSummary,StudyType,LeadSponsorName"
            ),
        }

        data = await self._get(f"{CT_API_BASE}/studies", params=params)
        studies = data.get("studies", [])

        results: list[MCPResult] = []
        for study in studies[:max_results]:
            try:
                result = self._parse_study(study, query)
                if result:
                    results.append(result)
            except Exception:
                logger.warning("Failed to parse a CT.gov study", exc_info=True)

        return results

    def _parse_study(self, study: dict, query: str) -> MCPResult | None:  # type: ignore[type-arg]
        """Parse a single CT.gov study entry."""
        proto = study.get("protocolSection", {})
        ident = proto.get("identificationModule", {})
        status = proto.get("statusModule", {})
        design = proto.get("designModule", {})
        desc = proto.get("descriptionModule", {})
        sponsor = proto.get("sponsorCollaboratorsModule", {})

        nct_id = ident.get("nctId", "")
        title = ident.get("briefTitle", "")

        # Enrollment
        enroll = design.get("enrollmentInfo", {})
        sample_size = None
        count_str = enroll.get("count")
        if count_str is not None:
            try:
                sample_size = int(count_str)
            except (ValueError, TypeError):
                pass

        # Conditions and interventions
        conditions = proto.get("conditionsModule", {})
        condition_list = conditions.get("conditions", [])
        interventions = proto.get("armsInterventionsModule", {})
        intervention_names: list[str] = []
        for iv in interventions.get("interventions", []):
            name = iv.get("name", "")
            if name:
                intervention_names.append(name)

        # Sponsor
        lead_sponsor = sponsor.get("leadSponsor", {})
        org_name = lead_sponsor.get("name", "")

        # Phases
        phases = design.get("phases", [])
        phase_str = ", ".join(phases) if phases else ""

        return MCPResult(
            title=title,
            authors=[],
            issuing_organization=org_name,
            publication_date=status.get("startDateStruct", {}).get("date", ""),
            trial_id=nct_id,
            canonical_url=f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
            study_type=f"clinical_trial ({phase_str})" if phase_str else "clinical_trial",
            population=", ".join(condition_list),
            sample_size=sample_size,
            intervention=", ".join(intervention_names),
            outcome=desc.get("briefSummary", ""),
            retraction_status="none",
            source_quality_tier=3,
            source_connector=self.connector_name,
            raw_id=nct_id,
            search_query=query,
            retrieval_timestamp=datetime.now(timezone.utc),
        )
