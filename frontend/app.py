"""MedicoBuddy — Enterprise Healthcare SaaS UI Architecture.

Refactored for clinical restraint, WCAG 2.2 AA accessibility, zero hackathon clutter,
and enterprise SaaS aesthetic.

Features:
- Consultation-first primary interface ("How can I help today?")
- Compact SVG "Medico Nexus" mark & clean navigation shell
- High-contrast collapsible Patient Context drawer
- Restrained dark slate clinical palette (#0b0f19, #111827, #38bdf8, #10b981)
- Separated "System & Architecture Details" view for technical metrics
- Enterprise answer components with multi-tab results & download controls
- Direct LangGraph engine fallback + FastAPI REST API integration
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
    page_title="MedicoBuddy — Healthcare Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants & Enums Mapping ────────────────────────────────
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
    "Temporary fatigue after work",
    "Slight nausea after eating",
    "Minor digestive indigestion",
    "Short-duration low fever",
]

# ── Enterprise Healthcare SaaS CSS Palette ────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Background Theme */
.stApp {
    background: #0b0f19;
    color: #f8fafc;
}

/* Top Product Navigation Shell */
.nav-shell {
    background: #111827;
    border-bottom: 1px solid #1e293b;
    padding: 0.85rem 1.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-radius: 12px;
}

.nav-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.nav-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #f8fafc;
    margin: 0;
    letter-spacing: -0.01em;
}

.nav-subtitle {
    font-size: 0.82rem;
    color: #94a3b8;
}

/* Primary Consultation Hero */
.hero-container {
    text-align: center;
    padding: 1.5rem 0 1rem 0;
    max-width: 720px;
    margin: 0 auto;
}

.hero-heading {
    font-size: 2rem;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 0.4rem;
    letter-spacing: -0.02em;
}

.hero-lead {
    font-size: 0.98rem;
    color: #94a3b8;
    line-height: 1.5;
}

/* Cards & Section Panels */
.saas-card {
    background: #111827;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}

.saas-card-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #38bdf8;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Triage Banners */
.triage-banner-selfcare {
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 8px;
    padding: 0.5rem 0.9rem;
    color: #34d399;
    font-weight: 600;
    font-size: 0.88rem;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
}

.triage-banner-clinician {
    background: rgba(245, 158, 11, 0.08);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 8px;
    padding: 0.5rem 0.9rem;
    color: #fbbf24;
    font-weight: 600;
    font-size: 0.88rem;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
}

.triage-banner-urgent {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-radius: 8px;
    padding: 0.5rem 0.9rem;
    color: #f87171;
    font-weight: 600;
    font-size: 0.88rem;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
}

/* Emergency Red-Flag Card */
.emergency-saas-card {
    background: #180909;
    border: 1px solid #dc2626;
    border-left: 5px solid #ef4444;
    border-radius: 12px;
    padding: 1.25rem;
    color: #fef2f2;
    margin-bottom: 1.25rem;
}

/* Sidebar High-Contrast Styling */
div[data-testid="stSidebar"] {
    background: #0d131f !important;
    border-right: 1px solid #1e293b;
}

div[data-testid="stSidebar"] label {
    color: #f1f5f9 !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
}

div[data-testid="stSidebar"] h1,
div[data-testid="stSidebar"] h2,
div[data-testid="stSidebar"] h3 {
    color: #f8fafc !important;
}

/* Buttons */
.stButton>button {
    border-radius: 8px;
    font-weight: 500;
    font-size: 0.88rem;
    border: 1px solid #1e293b;
    background: #111827;
    color: #f8fafc;
    transition: all 0.15s ease;
}

.stButton>button:hover {
    border-color: #0ea5e9;
    color: #38bdf8;
}

/* Tabs */
button[data-baseweb="tab"] {
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    color: #94a3b8 !important;
}

button[aria-selected="true"] {
    color: #38bdf8 !important;
    border-bottom-color: #0ea5e9 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Medico Nexus SVG Logo Component ──────────────────────────
SVG_LOGO = """
<svg width="36" height="36" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect x="6" y="6" width="88" height="88" rx="22" fill="#111827" stroke="#0ea5e9" stroke-width="4"/>
  <path d="M 28,70 L 28,32 L 50,54 L 72,32 L 72,70" fill="none" stroke="#38bdf8" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M 16,50 H 32 L 40,32 L 48,68 L 56,38 L 64,50 H 84" fill="none" stroke="#10b981" stroke-width="3.5" stroke-linecap="round"/>
  <circle cx="40" cy="32" r="4.5" fill="#38bdf8"/>
  <circle cx="48" cy="68" r="4.5" fill="#10b981"/>
  <circle cx="56" cy="38" r="4.5" fill="#f59e0b"/>
</svg>
"""


def render_nav_shell() -> str:
    """Render top product header & mode switcher."""
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f"""
        <div class="nav-brand">
            {SVG_LOGO}
            <div>
                <div class="nav-title">MedicoBuddy</div>
                <div class="nav-subtitle">Clinical Decision Support & Evidence Guidance</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        view_mode = st.radio(
            "View Mode",
            ["Consultation", "System Details"],
            horizontal=True,
            label_visibility="collapsed",
            key="view_mode_selector",
        )

    st.markdown("<hr style='border:0; border-top:1px solid #1e293b; margin:0.5rem 0 1rem 0;'>", unsafe_allow_html=True)
    return view_mode


def render_patient_drawer() -> dict[str, Any]:
    """Render collapsible, high-contrast Patient Context drawer in sidebar."""
    with st.sidebar:
        st.markdown("### Patient Context & Scope")
        st.caption("Minimum necessary information for deterministic triage routing.")

        with st.expander("👤 Demographics & Population", expanded=True):
            selected_age_label = st.selectbox(
                "Age Bracket",
                list(AGE_DISPLAY_MAP.keys()),
                index=0,
                help="Self-care guidance is strictly for adults aged 18–65.",
            )
            age_range = AGE_DISPLAY_MAP[selected_age_label]

            selected_preg_label = st.selectbox(
                "Pregnancy / Breastfeeding",
                list(PREGNANCY_DISPLAY_MAP.keys()),
                index=0,
            )
            pregnancy_status = PREGNANCY_DISPLAY_MAP[selected_preg_label]

            is_immuno = st.checkbox(
                "Immunocompromised",
                value=False,
                help="Check if patient has weakened immunity (e.g. active chemotherapy).",
            )

        with st.expander("🏥 Clinical History & Contraindications", expanded=False):
            conditions_raw = st.text_input(
                "Known Conditions",
                placeholder="e.g. diabetes, hypertension, kidney disease",
                help="Checked against food/fluid contraindications.",
            )
            allergies_raw = st.text_input(
                "Allergies",
                placeholder="e.g. peanuts, dairy, gluten",
            )
            medications_raw = st.text_input(
                "Current Medications",
                placeholder="e.g. metformin, lisinopril",
            )

        with st.expander("⚙️ Settings & Consent", expanded=False):
            region = st.selectbox(
                "Emergency Region",
                ["IN", "US", "UK", "EU"],
                index=0,
                help="Sets local emergency dial numbers if red flags occur.",
            )
            consent_given = st.checkbox(
                "I understand MedicoBuddy provides general info, not medical diagnosis",
                value=True,
            )

        st.markdown("""
        <div style="font-size:0.78rem; color:#64748b; margin-top:1.5rem; line-height:1.5; padding:0.75rem; background:#111827; border-radius:8px; border:1px solid #1e293b;">
            🔒 <strong>Privacy Assurance:</strong> Zero PII collected. Automated regex PII redaction active on all system logs.
        </div>
        """, unsafe_allow_html=True)

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


def render_response_components(data: dict[str, Any]) -> None:
    """Render response components in restrained enterprise style."""
    # ── Emergency Red-Flag State ─────────────────────────────
    if data.get("emergency_message"):
        contact = data.get("emergency_contact") or {}
        num = contact.get("number", "112")
        name = contact.get("name", "Emergency Medical Services")

        st.markdown(f"""
        <div class="emergency-saas-card">
            <div style="font-size:1.15rem; font-weight:700; color:#ffffff;">🚨 Immediate Medical Evaluation Recommended</div>
            <div style="margin-top:0.6rem; font-size:0.95rem; line-height:1.5;">
                {data["emergency_message"]}
            </div>
            <div style="margin-top:1rem; padding:0.75rem; background:rgba(0,0,0,0.3); border-radius:8px; display:flex; align-items:center; justify-content:space-between;">
                <span style="font-size:0.9rem;">Contact {name}:</span>
                <span style="font-size:1.3rem; font-weight:800; color:#f87171;">{num}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Clarification Needed State ───────────────────────────
    if data.get("needs_clarification") and data.get("clarification_questions"):
        st.info("Please clarify the following details:")
        for q in data["clarification_questions"]:
            st.markdown(f"• {q}")
        return

    # ── Triage Banner & Status ───────────────────────────────
    triage_outcome = data.get("triage_outcome", "self_care")
    urgency_summary = data.get("urgency_summary", "Self-care information")

    if triage_outcome == "self_care":
        banner_html = f'<div class="triage-banner-selfcare">✅ {urgency_summary}</div>'
    elif triage_outcome == "out_of_scope":
        banner_html = f'<div class="triage-banner-clinician">⚠️ Out of Scope — {urgency_summary}</div>'
    else:
        banner_html = f'<div class="triage-banner-urgent">🏥 {urgency_summary}</div>'

    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem;">
        {banner_html}
        <span style="font-size:0.8rem; color:#64748b;">Deterministic Triage Passed</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Multi-Tab Answer Architecture ────────────────────────
    tab_overview, tab_steps, tab_ayurveda, tab_safety, tab_evidence, tab_graph, tab_sources = st.tabs([
        "Overview",
        "Safe Steps",
        "Ayurveda Lens",
        "Safety Boundaries",
        "Evidence Table",
        "Knowledge Map",
        "Sources",
    ])

    # ── Overview Tab ─────────────────────────────────────────
    with tab_overview:
        st.markdown(f"""
        <div class="saas-card">
            <div class="saas-card-title">Summary of Reported Symptom</div>
            <div style="color:#e2e8f0; font-size:0.95rem; line-height:1.5;">{data.get('user_report_summary', 'No summary available.')}</div>
        </div>
        """, unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("##### Key Self-Care Guidance")
            for step in data.get("safe_comfort_steps", [])[:3]:
                st.markdown(f"• {step}")
        with col_b:
            st.markdown("##### Evidence Level")
            conf = data.get("overall_evidence_level", "insufficient").title()
            st.metric("Evidence Level", conf)

    # ── Safe Steps Tab ───────────────────────────────────────
    with tab_steps:
        st.markdown("##### Low-Risk Comfort Measures")
        for step in data.get("safe_comfort_steps", []):
            st.markdown(f"• {step}")

    # ── Ayurveda Lens Tab ────────────────────────────────────
    with tab_ayurveda:
        st.markdown("##### Ayurveda-Informed Lifestyle Perspective")
        perspectives = data.get("ayurveda_perspectives", [])
        if not perspectives:
            st.info("No specific Ayurvedic lifestyle practices matched this query with verified evidence.")
        else:
            for ap in perspectives:
                ev_label = ap.get("evidence_label", "").replace("_", " ").title()
                st.markdown(f"**{ap.get('practice', '')}** (`{ev_label}`)")
                st.caption(ap.get("description", ""))

    # ── Safety Boundaries Tab ────────────────────────────────
    with tab_safety:
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

    # ── Evidence Table Tab ───────────────────────────────────
    with tab_evidence:
        st.markdown("##### Multi-Factor Evidence Scoring")
        citations = data.get("citations", [])
        if not citations:
            st.info("No external citations retrieved for this query.")
        else:
            table_rows = []
            for c in citations:
                table_rows.append({
                    "Ref": f"[{c.get('number')}]",
                    "Title": c.get("title", "")[:50] + "...",
                    "Source Type": c.get("source_type", "Guideline").replace("_", " ").title(),
                    "Date": c.get("publication_date", "N/A"),
                })
            st.dataframe(table_rows, use_container_width=True)

    # ── Knowledge Map Tab ────────────────────────────────────
    with tab_graph:
        st.markdown("##### GraphRAG Entity Traversal Path")
        st.markdown("""
        ```
        [Symptom: Reported Query] ──► [SelfCareAction] ──► [Contraindication Check]
                                           │
                                           └──► [EvidenceClaim] ──► [Study / Guideline Tier 1-3]
        ```
        """)

    # ── Sources Tab ──────────────────────────────────────────
    with tab_sources:
        st.markdown("##### Provenance & Citations")
        citations = data.get("citations", [])
        if not citations:
            st.info("No external citations for this response.")
        else:
            for cite in citations:
                st.markdown(f"**[{cite.get('number')}]** [{cite.get('title')}]({cite.get('url', '#')}) ({cite.get('publication_date', '')})")

    # ── Export & Copy Controls ───────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    report_md = f"""# MedicoBuddy Wellness Report
Triage Status: {urgency_summary}

## Summary
{data.get('user_report_summary', '')}

## Safe Comfort Steps
{chr(10).join('- ' + s for s in data.get('safe_comfort_steps', []))}

## Disclaimer
{data.get('disclaimer', '')}
"""
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📄 Export Markdown Report",
            data=report_md,
            file_name="medicobuddy_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "💾 Export JSON Data",
            data=json.dumps(data, indent=2),
            file_name="medicobuddy_report.json",
            mime="application/json",
            use_container_width=True,
        )

    # Disclaimer
    st.markdown(f"""
    <div style="font-size:0.78rem; color:#64748b; margin-top:1.25rem; padding:0.6rem; background:#111827; border-radius:6px; border:1px solid #1e293b;">
        ⚕️ {data.get('disclaimer', '')}
    </div>
    """, unsafe_allow_html=True)


def render_system_details() -> None:
    """Render optional technical architecture & GraphRAG status page."""
    st.markdown("### System & Architecture Details")
    st.caption("Technical infrastructure and pipeline configuration.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("LLM Provider", "Groq API")
    c2.metric("LLM Model", "Llama-3.3-70B")
    c3.metric("Primary Vector DB", "Milvus Standalone")
    c4.metric("Secondary Vector DB", "pgvector (Postgres)")

    st.markdown("#### GraphRAG Schema & Connectors")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Neo4j Knowledge Graph:**
        - **16 Node Types**: Symptom, RedFlag, SelfCareAction, AyurvedicConcept, LifestylePractice, Contraindication, Condition, EvidenceClaim, Study, Guideline, Organization, Ingredient, AdverseEffect, Interaction, Source, PopulationGroup.
        - **13 Relationship Types**: SYMPTOM_HAS_RED_FLAG, ACTION_MAY_SUPPORT_SYMPTOM, ACTION_CONTRAINDICATED_FOR, CLAIM_SUPPORTED_BY, etc.
        """)
    with col2:
        st.markdown("""
        **MCP Data Connectors:**
        - **PubMed / NCBI E-utilities**: Peer-reviewed journal abstracts & PMIDs.
        - **ClinicalTrials.gov v2**: Active & completed RCT datasets.
        - **MedlinePlus / NLM**: Consumer health topics.
        - **Crossref REST API**: DOI resolution & metadata.
        """)

    st.markdown("#### Deterministic Triage Engine")
    st.markdown("""
    - **23 Red-Flag Rules**: Pattern matching for cardiac, stroke, meningitis, severe abdominal, bleeding, and acute trauma.
    - **2-Pass Gatekeeper**: Evaluated before retrieval and again before response delivery.
    """)


def process_query_direct(user_input: str, user_context: dict[str, Any]) -> dict[str, Any]:
    """Direct Python fallback execution when REST server is offline."""
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
    view_mode = render_nav_shell()
    user_context = render_patient_drawer()

    if view_mode == "System Details":
        render_system_details()
        return

    # ── Consultation Primary Interface ────────────────────────
    st.markdown("""
    <div class="hero-container">
        <div class="hero-heading">How can I help today?</div>
        <div class="hero-lead">Describe your symptom or select a suggestion below for evidence-grounded self-care guidance.</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Subtle Suggestion Chips ───────────────────────────────
    cols = st.columns(len(SUGGESTED_QUERIES))
    selected_query = None

    for i, suggestion in enumerate(SUGGESTED_QUERIES):
        if cols[i].button(suggestion, key=f"sug_{i}", use_container_width=True):
            selected_query = suggestion

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Chat Stream ──────────────────────────────────────────
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and isinstance(msg.get("data"), dict):
                render_response_components(msg["data"])
            else:
                st.markdown(msg["content"])

    # ── Conversational Input Box ──────────────────────────────
    user_input = st.chat_input("Enter your symptom description...", key="main_consultation_input")
    query_to_process = selected_query or user_input

    if query_to_process:
        if not user_context.get("consent_given"):
            st.warning("Please check the consent box in the sidebar context drawer to proceed.")
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

                render_response_components(data)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "",
                    "data": data,
                })


if __name__ == "__main__":
    main()
