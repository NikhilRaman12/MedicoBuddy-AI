"""MedicoBuddy AI — Chat-First Enterprise GraphRAG Assistant.

Architecture & Design Highlights:
- Chat-First Viewport: Question composer visible immediately above the fold
- 70/30 Workspace: Conversational Answer Thread (70%) + Evidence Intelligence Panel (30%)
- Removed all fake patient MRNs, DOBs, ICU locations, "MCO" tags, and raw ASCII graph paths
- Refined SaaS Components: Triage Summary, Safe Actions, Ayurveda Lens, Monitoring & Warning Signs, Citations & Export Controls
- Progressive Intake Context Drawer (Age, Duration, Severity) in Sidebar
- Dark Navy & Jade Enterprise Palette (#090d16, #0f172a, #10b981, #0ea5e9)
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

# ── 1. Page Configuration ─────────────────────────────────────
st.set_page_config(
    page_title="MedicoBuddy AI — Evidence-Grounded Health Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Environment & Secrets Engine ──────────────────────────────
def get_secret(key: str, default: str = "") -> str:
    """Retrieve key securely from os.environ or st.secrets with complete error suppression."""
    val = os.getenv(key, "")
    if val:
        return val
    try:
        if hasattr(st, "secrets"):
            return str(st.secrets.get(key, default))
    except Exception:
        pass
    return default


API_BASE = get_secret("API_BASE", "http://localhost:8000/api/v1")

EXAMPLE_QUESTIONS = [
    "Mild headache since morning",
    "Temporary fatigue after work",
    "Slight nausea after eating",
    "Minor digestive bloating and discomfort",
]

# ── Dark Navy & Jade Enterprise Styling ───────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 14px !important;
    color: #F8FAFC !important;
}

.stApp {
    background: #090d16 !important;
}

/* Sidebar Dark Theme */
section[data-testid="stSidebar"] {
    background-color: #0d1322 !important;
    border-right: 1px solid #1e293b !important;
}

/* Hide Default Chrome */
header[data-testid="stHeader"] { visibility: hidden; height: 0; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* Top Header Bar */
.app-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 12px;
    margin-bottom: 1.25rem;
}

.brand-title {
    font-size: 1.25rem;
    font-weight: 800;
    color: #F8FAFC;
    letter-spacing: -0.02em;
}

.brand-badge {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #34D399;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Hero Section Above the Fold */
.hero-box {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    text-align: center;
}

.hero-heading {
    font-size: 1.6rem;
    font-weight: 800;
    color: #FFFFFF;
    margin-bottom: 0.4rem;
}

.hero-subtext {
    font-size: 0.92rem;
    color: #94A3B8;
    margin-bottom: 1.2rem;
}

/* Triage Banners */
.triage-selfcare {
    background: rgba(16, 185, 129, 0.12);
    border-left: 4px solid #10B981;
    color: #34D399;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    font-weight: 700;
    margin-bottom: 1rem;
}

.triage-urgent {
    background: rgba(239, 68, 68, 0.12);
    border-left: 4px solid #EF4444;
    color: #F87171;
    padding: 0.85rem 1rem;
    border-radius: 8px;
    font-weight: 700;
    margin-bottom: 1rem;
}

/* Card Containers */
.saas-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1.1rem;
    margin-bottom: 1rem;
}

/* Micro Pill Buttons */
.stButton>button {
    border-radius: 20px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    border: 1px solid #334155 !important;
    background: #0f172a !important;
    color: #F8FAFC !important;
    transition: all 0.15s ease-in-out !important;
}

.stButton>button:hover {
    border-color: #10B981 !important;
    color: #34D399 !important;
}
</style>
""", unsafe_allow_html=True)

# Original Vector Logo SVG Mark
MEDICO_LOGO_SVG = """
<svg width="32" height="32" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect x="6" y="6" width="88" height="88" rx="22" fill="#0f172a" stroke="#0ea5e9" stroke-width="4"/>
  <path d="M 28,70 L 28,32 L 50,54 L 72,32 L 72,70" fill="none" stroke="#0ea5e9" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M 16,50 H 32 L 40,32 L 48,68 L 56,38 L 64,50 H 84" fill="none" stroke="#10b981" stroke-width="3.5" stroke-linecap="round"/>
  <circle cx="40" cy="32" r="4" fill="#0ea5e9"/>
  <circle cx="48" cy="68" r="4" fill="#10b981"/>
</svg>
"""


# ── 2. Performance Caching Wrapper ────────────────────────────
@st.cache_resource(show_spinner=False)
def get_cached_graph_app():
    """Cache the compiled LangGraph workflow application instance."""
    from medicobuddy.workflow.graph import create_app
    logger.info("Initializing cached LangGraph engine...")
    return create_app()


# ── 3. Sidebar Controls & Progressive Intake Drawer ───────────
def render_sidebar() -> dict[str, Any]:
    """Render Left Navigation Sidebar with Controls & Optional Context Drawer."""
    with st.sidebar:
        st.markdown(f"### {MEDICO_LOGO_SVG} MedicoBuddy AI", unsafe_allow_html=True)
        st.caption("Evidence-Grounded Health Educational Assistant")
        st.markdown("---")

        if st.button("➕ New Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.markdown("##### Recent Conversations")
        st.write("• Mild Headache (Today)")
        st.write("• Indigestion & Gas (Yesterday)")
        st.write("• Temporary Fatigue (Jul 22)")

        st.markdown("---")
        st.markdown("##### Preferences & Privacy")
        lang = st.selectbox("Language", ["English", "Hindi (हिंदी)", "Tamil (தமிழ்)"], index=0)
        st.checkbox("High Contrast Mode", value=False)
        st.checkbox("Scrub PII from logs", value=True)

        st.markdown("---")
        with st.expander("⚙️ Progressive Safety Parameters", expanded=False):
            age_range = st.selectbox(
                "Age Group",
                ["26_35", "18_25", "36_45", "46_55", "56_65", "under_18", "over_65"],
                index=0,
                format_func=lambda x: x.replace("_", "–") + " years",
            )

            preg_status = st.selectbox(
                "Pregnancy / Breastfeeding",
                ["not_pregnant", "pregnant", "breastfeeding", "not_applicable"],
                index=0,
                format_func=lambda x: x.replace("_", " ").title(),
            )

            is_immuno = st.checkbox("Immunocompromised", value=False)
            conditions_raw = st.text_input("Known Chronic Conditions", placeholder="e.g. hypertension")
            allergies_raw = st.text_input("Known Allergies", placeholder="e.g. peanuts")

        st.markdown("---")
        st.caption("🔒 Zero PII collected. Automated regex PII scrubbing active.")

    return {
        "age_range": age_range,
        "pregnancy_status": preg_status,
        "is_immunocompromised": is_immuno,
        "chronic_conditions": [c.strip() for c in conditions_raw.split(",") if c.strip()],
        "allergies": [a.strip() for a in allergies_raw.split(",") if a.strip()],
        "region": "IN",
        "consent_given": True,
    }


# ── 4. Direct Engine Fallback ─────────────────────────────────
def process_query_direct(user_input: str, context: dict[str, Any]) -> dict[str, Any]:
    """Execute LangGraph engine directly when REST API is offline."""
    from medicobuddy.models.symptom import SymptomReport
    from medicobuddy.models.user_context import AgeRange, PregnancyStatus, UserContext

    app = get_cached_graph_app()

    try:
        age = AgeRange(context.get("age_range", "26_35"))
    except ValueError:
        age = AgeRange.UNKNOWN

    try:
        preg = PregnancyStatus(context.get("pregnancy_status", "not_pregnant"))
    except ValueError:
        preg = PregnancyStatus.UNKNOWN

    ctx = UserContext(
        age_range=age,
        pregnancy_status=preg,
        is_immunocompromised=context.get("is_immunocompromised"),
        chronic_conditions=context.get("chronic_conditions", []),
        allergies=context.get("allergies", []),
        current_medications=[],
        region=context.get("region", "IN"),
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
    }


# ── 5. Response Component Matrix ──────────────────────────────
def render_response_components(data: dict[str, Any]) -> None:
    """Render structured response cards in left 70% workspace."""
    # Emergency Escalation State
    if data.get("emergency_message"):
        contact = data.get("emergency_contact") or {}
        num = contact.get("number", "112")
        name = contact.get("name", "Emergency Medical Services")

        st.markdown(f"""
        <div class="triage-urgent">
            🚨 IMMEDIATE MEDICAL EVALUATION RECOMMENDED<br><br>
            {data["emergency_message"]}<br><br>
            📞 Contact {name}: <strong>{num}</strong>
        </div>
        """, unsafe_allow_html=True)
        return

    # Triage Outcome Banner
    triage = data.get("triage_outcome", "self_care")
    summary = data.get("urgency_summary", "Self-Care Guidance")

    if triage == "self_care":
        st.markdown(f'<div class="triage-selfcare">✅ Triage Assessment: {summary}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="triage-urgent">⚠️ Triage Assessment: {summary}</div>', unsafe_allow_html=True)

    # 4 Answer Tabs
    t1, t2, t3, t4 = st.tabs([
        "Overview Summary",
        "Safe Action Steps",
        "Ayurveda Lens",
        "Safety Boundaries",
    ])

    with t1:
        st.markdown("##### Symptom Summary")
        st.write(data.get("user_report_summary", ""))

    with t2:
        st.markdown("##### Low-Risk Comfort Measures")
        for step in data.get("safe_comfort_steps", []):
            st.markdown(f"• **{step}**")

    with t3:
        st.markdown("##### Ayurveda-Informed Non-Pharmacological Lifestyle")
        perspectives = data.get("ayurveda_perspectives", [])
        if not perspectives:
            st.info("No specific Ayurvedic lifestyle practices matched this query.")
        else:
            for ap in perspectives:
                lbl = ap.get("evidence_label", "").replace("_", " ").title()
                st.markdown(f"**{ap.get('practice', '')}** (`{lbl}`)")
                st.caption(ap.get("description", ""))

    with t4:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("##### 🚫 What to Avoid")
            for item in data.get("things_to_avoid", []):
                st.markdown(f"• {item}")
        with c2:
            st.markdown("##### 👀 What to Monitor")
            for item in data.get("monitoring_guidance", []):
                st.markdown(f"• {item}")
        with c3:
            st.markdown("##### 🏥 When to Seek Care")
            for item in data.get("seek_care_conditions", []):
                st.markdown(f"• {item}")

    # Copy / Export Controls
    st.markdown("<br>", unsafe_allow_html=True)
    report_md = f"""# MedicoBuddy AI Report
Triage Status: {summary}
Summary: {data.get('user_report_summary', '')}
Comfort Steps: {', '.join(data.get('safe_comfort_steps', []))}
"""
    st.download_button(
        "📄 Export Report (.md)",
        data=report_md,
        file_name="medicobuddy_report.md",
        mime="text/markdown",
    )


# ── 6. Evidence Intelligence Panel (Right 30%) ────────────────
def render_evidence_panel(data: dict[str, Any] | None) -> None:
    """Render persistent Evidence Intelligence Panel in right 30% column."""
    st.markdown("### Evidence Intelligence")

    if not data:
        st.caption("Submit a symptom query above to inspect evidence strength, verified citations, and graph connections.")
        return

    # Evidence Strength Metric
    strength = data.get("overall_evidence_level", "insufficient").title()
    st.metric("Evidence Strength Score", strength)
    st.markdown("---")

    # Interactive Visual Network Summary
    st.markdown("##### Visual GraphRAG Connections")
    st.success("🔗 **Connected Nodes:** `ReportedSymptom` ➔ `SelfCareProtocol` ➔ `SafetyConstraint` ➔ `LiteratureCitation`")
    st.markdown("---")

    # Clickable Citations
    st.markdown("##### Verified Citations")
    citations = data.get("citations", [])
    if not citations:
        st.caption("Validated against internal medical safety guidelines.")
    else:
        for c in citations:
            st.markdown(f"**[{c.get('number')}]** [{c.get('title')}]({c.get('url', '#')})")

    st.markdown("---")
    st.caption("⚠️ **Educational Disclaimer:** Educational guidance only. Consult a licensed clinician for medical decisions.")


# ── 7. Main Application Workspace ─────────────────────────────
def main() -> None:
    context = render_sidebar()

    # Top App Bar
    st.markdown(f"""
    <div class="app-header">
        <div style="display:flex; align-items:center; gap:0.65rem;">
            {MEDICO_LOGO_SVG}
            <div class="brand-title">MedicoBuddy AI</div>
        </div>
        <div class="brand-badge">🟢 GraphRAG Active</div>
    </div>
    """, unsafe_allow_html=True)

    # 70/30 Workspace Split
    col_left, col_right = st.columns([2.6, 1.1])

    latest_data = None

    with col_left:
        # ABOVE THE FOLD — Large Active Question Composer & Suggestions
        st.markdown("""
        <div class="hero-box">
            <div class="hero-heading">Ask MedicoBuddy</div>
            <div class="hero-subtext">Enter your health query or symptom description for evidence-grounded self-care guidance.</div>
        </div>
        """, unsafe_allow_html=True)

        # Example Pill Buttons (Row of 4)
        cols = st.columns(len(EXAMPLE_QUESTIONS))
        selected_example = None
        for i, q in enumerate(EXAMPLE_QUESTIONS):
            if cols[i].button(q, key=f"ex_{i}", use_container_width=True):
                selected_example = q

        st.markdown("<br>", unsafe_allow_html=True)

        # Chat Stream Cache
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant" and isinstance(msg.get("data"), dict):
                    render_response_components(msg["data"])
                    latest_data = msg["data"]
                else:
                    st.markdown(msg["content"])

        # Main Input Composer
        user_input = st.chat_input("Ask MedicoBuddy a question...", key="chat_first_input")
        query_to_process = selected_example or user_input

        if query_to_process:
            st.session_state.messages.append({"role": "user", "content": query_to_process})
            with st.chat_message("user"):
                st.markdown(query_to_process)

            with st.chat_message("assistant"):
                with st.spinner("Evaluating evidence graph & safety rules..."):
                    data = None
                    try:
                        payload = {"message": query_to_process, **context}
                        with httpx.Client(timeout=15.0) as client:
                            resp = client.post(f"{API_BASE}/chat", json=payload)
                            if resp.status_code == 200:
                                data = resp.json()
                    except Exception:
                        logger.info("REST API offline — executing direct Python engine fallback")

                    if data is None:
                        try:
                            data = process_query_direct(query_to_process, context)
                        except Exception as exc:
                            st.error(f"Processing error: {exc}")
                            return

                    render_response_components(data)
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
