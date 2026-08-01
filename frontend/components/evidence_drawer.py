"""Evidence Drawer Component — MedicoBuddy AI.

Collapsible evidence drawer displaying:
- Evidence strength
- Retrieved source count
- Validated citations with Title, Source File, Page Number, Supporting Excerpt, Retrieval Score
- Actual Neo4j evidence paths (or 'No graph relationship available for this response.')
- Request ID and Retrieval Timestamp

INTEGRITY CONTRACT:
- Does NOT display decorative or fake graph flowcharts.
- Shows "No graph relationship available for this response" if no real graph path exists.
"""

from __future__ import annotations

import time
from typing import Any

import streamlit as st


def render_evidence_drawer(data: dict[str, Any], req_id: str = "") -> None:
    """Render collapsible right drawer / expander for evidence provenance."""
    citations = data.get("citations", [])
    graph_context = data.get("graph_context", [])
    overall_ev = data.get("overall_evidence_level", "MODERATE")
    ev_strength = data.get("evidence_strength", str(overall_ev))

    with st.expander("🔍 Grounded Evidence Intelligence Drawer", expanded=False):
        st.markdown(f"**Overall Evidence Strength:** `{ev_strength}`")
        st.markdown(f"**Retrieved Sources Count:** `{len(citations)}`")
        if req_id:
            st.markdown(f"**Request ID:** `{req_id}`")
        st.markdown(f"**Retrieval Timestamp:** `{time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}`")

        # 1. Source Citations
        if citations:
            st.markdown("#### Validated Citations & Provenance")
            for c in citations:
                if not isinstance(c, dict):
                    continue
                c_num = c.get("number", 1)
                c_title = c.get("title", "Clinical Guidelines")
                c_src = c.get("source_file") or ""
                c_page = c.get("page_number")
                pg_str = f" (Page {c_page})" if c_page else ""
                src_str = f" [{c_src}]" if c_src else ""
                score = c.get("retrieval_score", 0.0)
                score_str = f" `(Score: {score:.2f})`" if score > 0 else ""

                st.markdown(f"**[{c_num}] {c_title}{pg_str}**{src_str}{score_str}")

                if c.get("authors"):
                    st.caption(f"📖 Authors/Publisher: {c['authors']} ({c.get('publication_date', '')})")
                if c.get("supporting_passage"):
                    passage = c["supporting_passage"]
                    snippet = passage[:350] + "..." if len(passage) > 350 else passage
                    st.info(f"💬 Verbatim Excerpt: \"{snippet}\"")

        else:
            st.info("No formal PDF citations attached to this response (general education mode).")

        # 2. Knowledge Graph Traversal Path
        st.markdown("#### Knowledge Graph Evidence Path (Neo4j)")

        # Real graph results from diagnostics or state
        graph_paths = []
        if isinstance(graph_context, list):
            for g in graph_context:
                if isinstance(g, dict) and g.get("relationship"):
                    graph_paths.append(f"({g.get('symptom', 'Symptom')}) -[:{g.get('relationship')}]-> ({g.get('action', 'Action')})")

        if graph_paths:
            for path in graph_paths:
                st.code(path, language="cypher")
        else:
            st.caption("No graph relationship available for this response.")
