"""Official MCP Client Adapter for MedicoBuddy AI."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from medicobuddy.mcp.server import handle_call_tool, handle_list_tools
from medicobuddy.models.mcp import MCPResult

logger = logging.getLogger(__name__)


class MCPClientAdapter:
    """Client adapter calling MCP tools over official protocol handlers."""

    def __init__(self) -> None:
        self._tools: list[str] = []
        self._is_initialized = False

    async def initialize(self) -> bool:
        """Perform MCP protocol handshake and tool listing."""
        try:
            tools = await handle_list_tools()
            self._tools = [t.name for t in tools]
            self._is_initialized = len(self._tools) > 0
            logger.info("MCP ClientAdapter initialized with %d tools", len(self._tools))
            return True
        except Exception as exc:
            logger.warning("MCP ClientAdapter initialization failed: %s", exc)
            self._is_initialized = False
            return False

    @property
    def is_active(self) -> bool:
        return self._is_initialized

    async def call_mcp_tool(self, tool_name: str, arguments: dict[str, Any]) -> list[MCPResult]:
        """Invoke MCP tool through protocol handler and parse TextContent JSON into MCPResult objects."""
        try:
            content_list = await asyncio.wait_for(handle_call_tool(tool_name, arguments), timeout=2.0)
            if not content_list:
                return []

            raw_text = getattr(content_list[0], "text", "")
            if not raw_text:
                return []

            parsed = json.loads(raw_text)
            results: list[MCPResult] = []

            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and "title" in item:
                        results.append(MCPResult.model_validate(item))
            elif isinstance(parsed, dict) and "title" in parsed:
                results.append(MCPResult.model_validate(parsed))

            return results
        except Exception as exc:
            logger.warning("MCP call_mcp_tool('%s') failed: %s", tool_name, exc)
            return []

    async def search_all(
        self,
        queries: list[str],
        max_results_per_source: int = 3,
    ) -> tuple[list[MCPResult], dict[str, str], list[str]]:
        """Concurrent evidence retrieval across MCP tools with per-source diagnostics."""
        all_results: list[MCPResult] = []
        retrieval_status: dict[str, str] = {}
        dependency_errors: list[str] = []
        seen_titles: set[str] = set()

        q = queries[0] if queries else "headache"
        tools_to_run = [
            ("search_local_evidence_registry", {"query": q, "max_results": max_results_per_source}),
            ("search_medlineplus", {"query": q, "max_results": max_results_per_source}),
            ("search_pubmed", {"query": q, "max_results": max_results_per_source}),
        ]

        tasks = [self.call_mcp_tool(t_name, args) for t_name, args in tools_to_run]
        gathered = await asyncio.gather(*tasks, return_exceptions=True)

        for (t_name, _), res_or_exc in zip(tools_to_run, gathered):
            if isinstance(res_or_exc, Exception):
                retrieval_status[t_name] = "failed"
                dependency_errors.append(f"{t_name}: {res_or_exc}")
            elif isinstance(res_or_exc, list):
                retrieval_status[t_name] = f"success ({len(res_or_exc)} items)"
                for r in res_or_exc:
                    if r.title and r.title.lower() not in seen_titles:
                        seen_titles.add(r.title.lower())
                        all_results.append(r)

        return all_results, retrieval_status, dependency_errors

    async def close(self) -> None:
        """Close client resources."""
        self._is_initialized = False
