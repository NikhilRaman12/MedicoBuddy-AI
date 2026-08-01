"""Backend Status Component — MedicoBuddy AI.

Reads actual backend health endpoints (/health/ready, /health/dependencies) with short TTL cache.
Displays honest mode badges:
- Green: All active-profile services ready
- Amber: Degraded but safe limited mode (e.g. local FAISS fallback)
- Red: Service unavailable
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from frontend.api_client import check_health_dependencies, check_health_ready


@st.cache_data(ttl=5.0)
def fetch_cached_status() -> tuple[dict[str, Any], dict[str, Any]]:
    """Fetch health ready and dependencies with 5s TTL cache."""
    ready_data = check_health_ready()
    deps_data = check_health_dependencies()
    return ready_data, deps_data


def render_status_badge() -> None:
    """Render status badge showing actual backend mode."""
    ready_data, deps_data = fetch_cached_status()

    is_ready = ready_data.get("ready", False)
    vector_status = ready_data.get("vector_db", "offline")
    mode_label = ready_data.get("active_profile", "LOCAL")

    if is_ready and vector_status == "connected":
        badge_html = f'<span class="mode-badge mode-badge-green">● Mode: {mode_label} (Ready)</span>'
    elif vector_status == "local_faiss_fallback" or (deps_data.get("overall") == "degraded"):
        badge_html = '<span class="mode-badge mode-badge-amber">● Mode: Degraded (Local FAISS Fallback)</span>'
    else:
        badge_html = '<span class="mode-badge mode-badge-red">● Mode: Service Offline</span>'

    st.markdown(badge_html, unsafe_allow_html=True)


def render_admin_diagnostics() -> None:
    """Render admin diagnostics inside sidebar expander."""
    ready_data, deps_data = fetch_cached_status()

    with st.expander("🛠️ Admin & System Diagnostics", expanded=False):
        st.markdown("#### Health Readiness")
        st.json(ready_data)

        st.markdown("#### Per-Service Dependencies")
        st.json(deps_data)
