"""MedicoBuddy — Enterprise Healthcare SaaS Workspace.

Architecture:
- Left Rail: Session History & Patient Context Drawer
- Central Workspace: 3-Stage Journey (Safety -> Retrieval -> Guidance), Chat Stream & SaaS Response Cards
- Right Intelligence Panel: Real-time Evidence Certainty, Graph-Path Preview & Provenance Citations
- Dark Navy / Jade Palette (#0a0f1d, #111827, #10b981, #0ea5e9) with WCAG 2.2 AA Compliance
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import httpx
import streamlit as st

logger = logging.getLogger(__name__)

# ── Page Configuration ───────────────────────────────────────
st.set_page_config(
    page_title="MedicoBuddy Workspace",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ────────────────────────────────────────────────
API_BASE = os.getenv("API_BASE", "http://localhost:8000/api/v1")

AGE_DISPLAY_MAP = {
    "26–35 years (Adult)": "26_35",
    "18–25 years (Adult)": "18_25",
    "36–45 years (Adult)": "36_45",
    "46–55 years (Adult)": "46_55",
    "56–65 years (Adult)": "56_65",
    "Under 18 years (Pediatric)": "under_18",
    "Over 65 years (Senior)": "over_65",
    "Not specified": "unknown",
}

PREGNANCY_DISPLAY_MAP = {
    "Not pregnant": "not_pregnant",
    "Not applicable": "not_applicable",
    "Pregnant": "pregnant",
    "Breastfeeding": "breastfeeding",
    "Not specified": "unknown",
}

SUGGESTED_QUERIES = [
    "Mild headache since morning",
    "Temporary tiredness after work",
    "Slight nausea after lunch",
    "Minor indigestion and stomach discomfort",
    "Short-duration low fever",
]

# ── Enterprise Navy & Jade CSS Styling ────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

/* Base App Dark Navy */
.stApp {
    background: #080c14;
    color: #f8fafc;
}

/* Left Sidebar Rail */
div[data-testid="stSidebar"] {
    background: #0d1322 !important;
    border-right: 1px solid #1e293b;
}

div[data-testid="stSidebar"] label,
div[data-testid="stSidebar"] p,
div[data-testid="stSidebar"] span,
div[data-testid="stSidebar"] div {
    color: #f1f5f9 !important;
}

div[data-testid="stSidebar"] .stSelectbox div,
div[data-testid="stSidebar"] .stTextInput input {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border: 1px solid #334155 !important;
}

/* Top Navigation Bar */
.top-nav-bar {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 0.75rem 1.25rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.brand-wrapper {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.brand-text {
    font-size: 1.15rem;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.01em;
}

/* 3-Stage Journey Indicator */
.journey-bar {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    margin-bottom: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1.5rem;
    font-size: 0.82rem;
    font-weight: 600;
}

.stage-step {
    color: #0ea5e9;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.stage-arrow {
    color: #475569;
}

/* Cards & Response Containers */
.saas-container {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1.15rem;
    margin-bottom: 1rem;
}

.saas-title {
    font-size: 0.92rem;
    font-weight: 600;
    color: #0ea5e9;
    margin-bottom: 0.5rem;
}

/* Status Banners */
.triage-banner-selfcare {
    background: rgba(16, 185, 129, 0.1);
    border-left: 4px solid #10b981;
    color: #34d399;
    padding: 0.6rem 0.9rem;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.88rem;
    margin-bottom: 1rem;
}

.triage-banner-urgent {
    background: rgba(239, 68, 68, 0.12);
    border-left: 4px solid #ef4444;
    color: #f87171;
    padding: 0.85rem 1rem;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.9rem;
    margin-bottom: 1rem;
}

/* Right Panel Evidence Card */
.evidence-panel-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 1rem;
}

.evidence-panel-title {
    font-size: 0.88rem;
    font-weight: 600;
    color: #10b981;
    margin-bottom: 0.6rem;
}

/* Buttons */
.stButton>button {
    border-radius: 8px;
    font-weight: 500;
    font-size: 0.85rem;
    border: 1px solid #1e293b;
    background: #0f172a;
    color: #f8fafc;
}

.stButton>button:hover {
    border-color: #0ea5e9;
    color: #0ea5e9;
}
</style>
""", unsafe_allow_html=True)


# ── Medico Nexus SVG Logo ───────────────────────────────────
SVG_LOGO = """
<svg width="28" height="28" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect x="6" y="6" width="88" height="88" rx="20" fill="#0f172a" stroke="#0ea5e9" stroke-width="4"/>
  <path d="M 28,70 L 28,32 L 50,54 L 72,32 L 72,70" fill="none" stroke="#0ea5e9" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M 16,50 H 32 L 40,32 L 48,68 L 56,38 L 64,50 H 84" fill="none" stroke="#10b981" stroke-width="3.5" stroke-linecap="round"/>
  <circle cx="40" cy="32" r="4.5" fill="#0ea5e9"/>
  <circle cx="48" cy="68" r="4.5" fill="#10b981"/>
</svg>
"""


def render_left_rail() -> dict[str, Any]:
    """Render Left Rail with Session History & Patient Context Drawer."""
    with st.sidebar:
        st.markdown("### Workspace")
        if st.button("➕ New Session", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.markdown("##### Recent Sessions")
        st.caption("• Mild Headache (Today)")
        st.caption("• Indigestion & Gas (Yesterday)")
        st.caption("• Temporary Fatigue (Jul 22)")

        st.markdown("---")
        st.markdown("##### Patient Context Drawer")

        with st.expander("👤 Context Parameters", expanded=False):
            selected_age_label = st.selectbox(
                "Age Bracket",
                list(AGE_DISPLAY_MAP.keys()),
                index=0,
            )
            age_range = AGE_DISPLAY_MAP[selected_age_label]

            selected_preg_label = st.selectbox(
                "Pregnancy Status",
                list(PREGNANCY_DISPLAY_MAP.keys()),
                index=0,
            )
            pregnancy_status = PREGNANCY_DISPLAY_MAP[selected_preg_label]

            is_immuno = st.checkbox("Immunocompromised", value=False)

            conditions_raw = st.text_input("Known Conditions", placeholder="e.g. diabetes")
            allergies_raw = st.text_input("Allergies", placeholder="e.g. peanuts")
            medications_raw = st.text_input("Medications", placeholder="e.g. metformin")

            region = st.selectbox("Region", ["IN", "US", "UK", "EU"], index=0)
            consent_given = st.checkbox("Consent Acknowledged", value=True)

        st.markdown("---")
        st.caption("🔒 Zero PII collected. Automated regex PII scrubbing active.")

    return {
        "age_range": age_range,
        "pregnancy_status": pregnancy_status,
        "is_immunocompromised": is_immuno,
        "chronic_conditions": [c.strip() for c in conditions_raw.split(",") if c.strip()],
        "allergies": [a.strip() for a in allergies_raw.split(",") if a.strip()],
        "current_medications": [m.strip() for m in medications_raw.split(",") if m.strip()],
        "region": region,
        "consent_given": consent_given,
    }


def render_response_workspace(data: dict[str, Any]) -> None:
    """Render central workspace answer components."""
    # ── Emergency State ──────────────────────────────────────
    if data.get("emergency_message"):
        contact = data.get("emergency_contact") or {}
        num = contact.get("number", "112")
        name = contact.get("name", "Emergency Medical Services")

        st.markdown(f"""
        <div class="triage-banner-urgent">
            🚨 IMMEDIATE MEDICAL EVALUATION RECOMMENDED<br><br>
            {data["emergency_message"]}<br><br>
            📞 Contact {name}: <strong>{num}</strong>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Clarification State ──────────────────────────────────
    if data.get("needs_clarification") and data.get("clarification_questions"):
        st.info("Clarification needed before proceeding:")
        for q in data["clarification_questions"]:
            st.markdown(f"• {q}")
        return

    # ── Triage Outcome Banner ────────────────────────────────
    triage_outcome = data.get("triage_outcome", "self_care")
    urgency_summary = data.get("urgency_summary", "Self-care information")

    if triage_outcome == "self_care":
        st.markdown(f'<div class="triage-banner-selfcare">✅ Triage Status: {urgency_summary}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="triage-banner-urgent">⚠️ Triage Status: {urgency_summary}</div>', unsafe_allow_html=True)

    # ── Answer Tabs ──────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "Overview",
        "Safe Comfort Steps",
        "Ayurveda Lens",
        "Safety Boundaries",
    ])

    with tab1:
        st.markdown(f"""
        <div class="saas-container">
            <div class="saas-title">Summary of Reported Symptom</div>
            <div>{data.get('user_report_summary', 'No summary available.')}</div>
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        st.markdown("##### Low-Risk Comfort Measures")
        for step in data.get("safe_comfort_steps", []):
            st.markdown(f"• {step}")

    with tab3:
        st.markdown("##### Ayurveda-Informed Lifestyle Practices")
        perspectives = data.get("ayurveda_perspectives", [])
        if not perspectives:
            st.info("No specific Ayurvedic lifestyle practices matched this query.")
        else:
            for ap in perspectives:
                ev_label = ap.get("evidence_label", "").replace("_", " ").title()
                st.markdown(f"**{ap.get('practice', '')}** (`{ev_label}`)")
                st.caption(ap.get("description", ""))

    with tab4:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("##### What to Avoid")
            for item in data.get("things_to_avoid", []):
                st.markdown(f"• {item}")
        with c2:
            st.markdown("##### What to Monitor")
            for item in data.get("monitoring_guidance", []):
                st.markdown(f"• {item}")
        with c3:
            st.markdown("##### When to Seek Care")
            for item in data.get("seek_care_conditions", []):
                st.markdown(f"• {item}")


def render_evidence_panel(data: dict[str, Any] | None) -> None:
    """Render persistent right-side Evidence Intelligence panel."""
    st.markdown("### Evidence Intelligence")

    if not data:
        st.caption("Submit a symptom query to inspect evidence sources, certainty score, and graph-path preview.")
        return

    # Certainty Meter
    conf = data.get("overall_evidence_level", "insufficient").title()
    st.metric("Evidence Certainty Score", conf)
    st.markdown("---")

    # Graph Traversal Path
    st.markdown("##### Graph-Path Preview")
    st.code("""
(Symptom) ──► (SelfCareAction)
   │
   ├──► (Contraindication Check)
   │
   └──► (EvidenceClaim)
    """, language="text")
    st.markdown("---")

    # Citations
    st.markdown("##### Verified MCP Sources")
    citations = data.get("citations", [])
    if not citations:
        st.caption("Deterministic safety rules applied.")
    else:
        for c in citations:
            st.markdown(f"**[{c.get('number')}]** [{c.get('title')}]({c.get('url', '#')})")

    st.markdown("---")
    # Export Controls
    st.markdown("##### Export Data")
    report_md = f"""# MedicoBuddy Report
Triage Status: {data.get('urgency_summary', '')}
Summary: {data.get('user_report_summary', '')}
"""
    st.download_button(
        "📄 Export Report (.md)",
        data=report_md,
        file_name="medicobuddy_report.md",
        mime="text/markdown",
        use_container_width=True,
    )


def process_query_direct(user_input: str, user_context: dict[str, Any]) -> dict[str, Any]:
    """Direct Python engine execution fallback."""
    from medicobuddy.models.symptom import SymptomReport
    from medicobuddy.models.user_context import AgeRange, PregnancyStatus, UserContext
    from medicobuddy.workflow.graph import create_app

    app = create_app()

    try:
        age = AgeRange(user_context.get("age_range", "26_35"))
    except ValueError:
        age = AgeRange.UNKNOWN

    try:
        preg = PregnancyStatus(user_context.get("pregnancy_status", "not_pregnant"))
    except ValueError:
        preg = PregnancyStatus.UNKNOWN

    ctx = UserContext(
        age_range=age,
        pregnancy_status=preg,
        is_immunocompromised=user_context.get("is_immunocompromised"),
        chronic_conditions=user_context.get("chronic_conditions", []),
        allergies=user_context.get("allergies", []),
        current_medications=user_context.get("current_medications", []),
        region=user_context.get("region", "IN"),
    )

    initial_state = {
        "user_message": user_input,
        "user_context": ctx,
        "symptom_report": SymptomReport(main_symptom=user_input),
        "conversation_history": [],
    }

    result = app.invoke(initial_state)
    final = result.get("final_response")

    if final is None:
        raise RuntimeError("Workflow failed to produce a final response")

    return {
        "triage_outcome": final.triage_outcome.value,
        "urgency_summary": final.urgency_summary,
        "user_report_summary": final.user_report_summary,
        "safe_comfort_steps": final.safe_comfort_steps,
        "ayurveda_perspectives": [
            {
                "practice": ap.practice,
                "description": ap.description,
                "evidence_label": ap.evidence_label,
            }
            for ap in final.ayurveda_perspectives
        ],
        "things_to_avoid": final.things_to_avoid,
        "monitoring_guidance": final.monitoring_guidance,
        "seek_care_conditions": final.seek_care_conditions,
        "overall_evidence_level": final.overall_evidence_level.value,
        "citations": [c.model_dump() for c in final.citations],
        "disclaimer": final.disclaimer,
        "emergency_message": final.emergency_message,
        "emergency_contact": final.emergency_contact,
        "clarification_questions": result.get("clarification_questions", []),
        "needs_clarification": result.get("needs_clarification", False),
    }


def main() -> None:
    """Main Application Controller."""
    user_context = render_left_rail()

    # Top Navigation Bar
    st.markdown(f"""
    <div class="top-nav-bar">
        <div class="brand-wrapper">
            {SVG_LOGO}
            <div class="brand-text">MedicoBuddy Workspace</div>
        </div>
        <div style="font-size:0.82rem; color:#94a3b8;">Enterprise Healthcare Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    # 3-Column Workspace Layout
    col_center, col_right = st.columns([2.8, 1.2])

    latest_data = None

    with col_center:
        # 3-Stage Journey Indicator
        st.markdown("""
        <div class="journey-bar">
            <span class="stage-step">✓ 1. Safety Check</span>
            <span class="stage-arrow">→</span>
            <span class="stage-step">✓ 2. Evidence Retrieval</span>
            <span class="stage-arrow">→</span>
            <span class="stage-step">✓ 3. Grounded Guidance</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### How can I help today?")
        st.caption("Enter your symptom description below for evidence-grounded self-care guidance.")

        # Suggestion Chips
        cols = st.columns(len(SUGGESTED_QUERIES))
        selected_query = None
        for i, suggestion in enumerate(SUGGESTED_QUERIES):
            if cols[i].button(suggestion, key=f"sug_{i}", use_container_width=True):
                selected_query = suggestion

        st.markdown("<br>", unsafe_allow_html=True)

        # Chat Stream
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant" and isinstance(msg.get("data"), dict):
                    render_response_workspace(msg["data"])
                    latest_data = msg["data"]
                else:
                    st.markdown(msg["content"])

        # Input Composer
        user_input = st.chat_input("Enter your symptom description...", key="main_workspace_input")
        query_to_process = selected_query or user_input

        if query_to_process:
            if not user_context.get("consent_given"):
                st.warning("Please acknowledge consent in the sidebar drawer to proceed.")
                return

            st.session_state.messages.append({"role": "user", "content": query_to_process})
            with st.chat_message("user"):
                st.markdown(query_to_process)

            with st.chat_message("assistant"):
                with st.spinner("Evaluating evidence graph & safety rules..."):
                    data = None
                    try:
                        payload = {"message": query_to_process, **user_context}
                        with httpx.Client(timeout=15.0) as client:
                            resp = client.post(f"{API_BASE}/chat", json=payload)
                            if resp.status_code == 200:
                                data = resp.json()
                    except Exception:
                        logger.info("REST API offline — using direct Python engine fallback")

                    if data is None:
                        try:
                            data = process_query_direct(query_to_process, user_context)
                        except Exception as e:
                            st.error(f"Processing error: {e}")
                            return

                    render_response_workspace(data)
                    latest_data = data
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "",
                        "data": data,
                    })

    with col_right:
        render_evidence_panel(latest_data)


if __name__ == "__main__":
    main()
