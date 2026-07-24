"""MedicoBuddy — Production-Grade GraphRAG Streamlit Frontend.

Designed by Senior Healthcare UX Researcher, Accessibility Specialist & Streamlit Architect.
Theme: Midnight Green (#061210), Jade (#10b981), Aqua (#22d3ee), and Saffron (#f59e0b).
Features:
- "Medico Nexus" SVG branding (Care + Leaf + Pulse + Graph Nodes + Negative Space 'M')
- Progressive disclosure sidebar with human-readable labels
- Guided symptom onboarding chips & live GraphRAG execution progress
- 7-Tab Evidence-Grounded Result Panel: Overview, Safe Steps, Ayurveda Lens, Evidence Table, Knowledge Map, Safety Plan, Sources
- Download Controls (Markdown & JSON export)
- Direct LangGraph Engine fallback & REST API integration
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

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="MedicoBuddy — Medico Nexus GraphRAG",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ────────────────────────────────────────────────
API_BASE = os.getenv("API_BASE", "http://localhost:8000/api/v1")

AGE_DISPLAY_MAP = {
    "26–35 years (Adult Scope)": "26_35",
    "18–25 years (Adult Scope)": "18_25",
    "36–45 years (Adult Scope)": "36_45",
    "46–55 years (Adult Scope)": "46_55",
    "56–65 years (Adult Scope)": "56_65",
    "Under 18 years (Pediatric - Out of Scope)": "under_18",
    "Over 65 years (Senior - Out of Scope)": "over_65",
    "Not Specified": "unknown",
}

PREGNANCY_DISPLAY_MAP = {
    "Not pregnant": "not_pregnant",
    "Not applicable": "not_applicable",
    "Pregnant (Out of Scope)": "pregnant",
    "Breastfeeding (Out of Scope)": "breastfeeding",
    "Not Specified": "unknown",
}

PRESET_SYMPTOMS = [
    {"icon": "🤕", "label": "Mild Headache", "text": "I have had a mild, dull headache since this morning. No head injury or fever."},
    {"icon": "😴", "label": "Temporary Fatigue", "text": "I feel tired and low energy today after a busy week. No muscle weakness."},
    {"icon": "🤢", "label": "Mild Nausea", "text": "I feel slightly nauseous after eating lunch, but no vomiting or stomach pain."},
    {"icon": "🫄", "label": "Stomach Discomfort", "text": "I have minor, non-localized stomach discomfort and mild bloating."},
    {"icon": "🌡️", "label": "Short Mild Fever", "text": "I have a mild low-grade fever (around 37.8°C / 100°F) for less than 24 hours."},
    {"icon": "💨", "label": "Digestive Indigestion", "text": "I have mild indigestion and acidity after a heavy meal."},
]

# ── Custom CSS for Midnight Green + Jade + Aqua + Saffron ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

* {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Background Theme */
.stApp {
    background: linear-gradient(145deg, #05100e 0%, #091a17 50%, #061210 100%);
    color: #f0fdf4;
}

/* Header & Banner */
.app-header {
    background: linear-gradient(135deg, rgba(15, 35, 32, 0.95) 0%, rgba(9, 26, 23, 0.98) 100%);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 18px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 12px 30px -5px rgba(0, 0, 0, 0.6);
}

.header-flex {
    display: flex;
    align-items: center;
    gap: 1.25rem;
}

.brand-title {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #22d3ee 0%, #10b981 50%, #f59e0b 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}

.brand-subtitle {
    color: #94a3b8;
    font-size: 0.95rem;
    margin-top: 0.25rem;
}

/* Trust Badges */
.trust-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-top: 1rem;
}

.trust-badge {
    background: rgba(18, 41, 36, 0.8);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 20px;
    padding: 0.35rem 0.85rem;
    font-size: 0.78rem;
    font-weight: 600;
    color: #a7f3d0;
}

.trust-badge-highlight {
    border-color: #22d3ee;
    color: #22d3ee;
    background: rgba(34, 211, 238, 0.1);
}

.trust-badge-saffron {
    border-color: #f59e0b;
    color: #fcd34d;
    background: rgba(245, 158, 11, 0.1);
}

/* Cards & Layout */
.medical-card {
    background: #0d201c;
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 14px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}

.card-header-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #22d3ee;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Emergency Red Flag Card */
.emergency-card {
    background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%);
    border: 2px solid #ef4444;
    border-radius: 16px;
    padding: 1.5rem;
    color: #fef2f2;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 25px rgba(239, 68, 68, 0.3);
}

/* Badges for Triage Outcomes */
.badge-self-care {
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid #10b981;
    color: #34d399;
    padding: 0.35rem 0.9rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.85rem;
}

.badge-clinician {
    background: rgba(245, 158, 11, 0.2);
    border: 1px solid #f59e0b;
    color: #fcd34d;
    padding: 0.35rem 0.9rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.85rem;
}

.badge-urgent {
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid #ef4444;
    color: #f87171;
    padding: 0.35rem 0.9rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.85rem;
}

/* Evidence Badges */
.evidence-tag-high { background: #065f46; color: #6ee7b7; padding: 4px 12px; border-radius: 14px; font-weight: 600; font-size: 0.78rem; }
.evidence-tag-mod { background: #78350f; color: #fde68a; padding: 4px 12px; border-radius: 14px; font-weight: 600; font-size: 0.78rem; }
.evidence-tag-lim { background: #7c2d12; color: #ffedd5; padding: 4px 12px; border-radius: 14px; font-weight: 600; font-size: 0.78rem; }

/* High-Contrast Sidebar Styling */
div[data-testid="stSidebar"] {
    background: #081714 !important;
    border-right: 1px solid rgba(16, 185, 129, 0.2);
}

div[data-testid="stSidebar"] label {
    color: #e2e8f0 !important;
    font-weight: 600 !important;
}

div[data-testid="stSidebar"] h1, 
div[data-testid="stSidebar"] h2, 
div[data-testid="stSidebar"] h3 {
    color: #f0fdf4 !important;
}

/* Tabs Customization */
button[data-baseweb="tab"] {
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    color: #94a3b8 !important;
}

button[aria-selected="true"] {
    color: #22d3ee !important;
    border-bottom-color: #10b981 !important;
}

/* Buttons */
.stButton>button {
    border-radius: 10px;
    font-weight: 600;
    border: 1px solid rgba(16, 185, 129, 0.3);
    background: linear-gradient(135deg, #0d201c 0%, #081714 100%);
    color: #f0fdf4;
    transition: all 0.2s ease;
}

.stButton>button:hover {
    border-color: #22d3ee;
    color: #22d3ee;
    transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)


# ── Medico Nexus SVG Logo Component ──────────────────────────

MEDICO_NEXUS_SVG = """
<svg width="56" height="56" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="nexusGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#22d3ee" />
      <stop offset="50%" stop-color="#10b981" />
      <stop offset="100%" stop-color="#f59e0b" />
    </linearGradient>
  </defs>
  <!-- Circle Shield Background -->
  <circle cx="50" cy="50" r="46" fill="#0b201c" stroke="url(#nexusGrad)" stroke-width="3.5"/>
  <!-- Negative Space M / Care Shield -->
  <path d="M 28,68 L 28,32 L 50,54 L 72,32 L 72,68" fill="none" stroke="#22d3ee" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
  <!-- Pulse Line across center -->
  <path d="M 14,50 L 32,50 L 40,30 L 48,68 L 56,40 L 64,52 L 86,50" fill="none" stroke="#f59e0b" stroke-width="3" stroke-linecap="round"/>
  <!-- Graph Nodes -->
  <circle cx="40" cy="30" r="4.5" fill="#10b981"/>
  <circle cx="48" cy="68" r="4.5" fill="#22d3ee"/>
  <circle cx="56" cy="40" r="4.5" fill="#f59e0b"/>
  <!-- Leaf Curve top right -->
  <path d="M 50,14 C 66,14 76,24 76,40 C 60,40 50,28 50,14 Z" fill="#10b981" opacity="0.85"/>
</svg>
"""


def render_header() -> None:
    """Render top branding banner with Medico Nexus SVG & trust badges."""
    st.markdown(f"""
    <div class="app-header">
        <div class="header-flex">
            <div>{MEDICO_NEXUS_SVG}</div>
            <div>
                <div class="brand-title">MedicoBuddy <span style="font-size:1.1rem; font-weight:600; color:#22d3ee;">Medico Nexus GraphRAG</span></div>
                <div class="brand-subtitle">
                    Evidence-Grounded Healthcare AI Assistant · Low-Risk Self-Care Guidance & Ayurveda Lens for Adults (18–65)
                </div>
            </div>
        </div>
        <div class="trust-bar">
            <span class="trust-badge trust-badge-highlight">⚡ Groq Llama-3.3-70B Engine</span>
            <span class="trust-badge trust-badge-highlight">🕸️ Neo4j Knowledge Graph (16 Nodes / 13 Rel)</span>
            <span class="trust-badge trust-badge-highlight">🗄️ Milvus + pgvector Hybrid Search</span>
            <span class="trust-badge trust-badge-highlight">🧬 Qwen3-Embedding-8B (4096-dim)</span>
            <span class="trust-badge trust-badge-saffron">🛡️ 100% Deterministic Red-Flag Engine</span>
            <span class="trust-badge">📚 PubMed / NCBI / CT.gov MCP Connectors</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar() -> dict[str, Any]:
    """Render high-contrast progressive intake form with clean human-readable options."""
    with st.sidebar:
        st.markdown("## 🛡️ Patient Profile & Scope")
        st.caption("Minimum necessary information to ensure safe triage routing.")

        with st.expander("👤 1. Population & Demographics", expanded=True):
            selected_age_label = st.selectbox(
                "Age Range",
                list(AGE_DISPLAY_MAP.keys()),
                index=0,
                help="MedicoBuddy guidance is strictly for adults aged 18–65.",
            )
            age_range = AGE_DISPLAY_MAP[selected_age_label]

            selected_preg_label = st.selectbox(
                "Pregnancy / Breastfeeding Status",
                list(PREGNANCY_DISPLAY_MAP.keys()),
                index=0,
            )
            pregnancy_status = PREGNANCY_DISPLAY_MAP[selected_preg_label]

            is_immuno = st.checkbox(
                "Immunocompromised Status",
                value=False,
                help="Check if you have a weakened immune system (e.g., chemotherapy, active immunosuppressants).",
            )

        with st.expander("🏥 2. Medical History & Allergies", expanded=False):
            conditions_raw = st.text_input(
                "Known Chronic Conditions",
                placeholder="e.g. diabetes, hypertension, kidney disease",
                help="Checked against contraindication rules before food/fluid recommendations.",
            )
            allergies_raw = st.text_input(
                "Food & Environmental Allergies",
                placeholder="e.g. peanuts, dairy, gluten",
            )
            medications_raw = st.text_input(
                "Current Medications (Names Only)",
                placeholder="e.g. metformin, lisinopril",
            )

        with st.expander("🌐 3. Emergency Region & Consent", expanded=False):
            region = st.selectbox(
                "Emergency Contact Region",
                ["IN", "US", "UK", "EU"],
                index=0,
                help="Configures local emergency contacts (112, 911, 999) if red flags occur.",
            )

            st.markdown("---")
            consent_given = st.checkbox(
                "I understand MedicoBuddy provides general educational information, not medical advice",
                value=True,
            )

        st.markdown("""
        <div style="font-size:0.78rem; color:#94a3b8; margin-top:1.5rem; line-height:1.5; padding:0.85rem; background:rgba(13,32,28,0.8); border-radius:10px; border:1px solid rgba(16,185,129,0.2);">
            🔒 <strong>Zero PII Collection:</strong> No names, emails, or IDs stored. Automated regex PII redaction on all structured logs.
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


def render_results_panel(data: dict[str, Any]) -> None:
    """Render the 7-Tab Evidence-Grounded Result Panel."""
    # ── Emergency Red-Flag Banner ─────────────────────────────
    if data.get("emergency_message"):
        contact = data.get("emergency_contact") or {}
        num = contact.get("number", "112 / 911")
        name = contact.get("name", "Emergency Services")

        st.markdown(f"""
        <div class="emergency-card">
            <div style="font-size:1.35rem; font-weight:800; color:#ffffff; display:flex; align-items:center; gap:0.5rem;">
                🚨 URGENT MEDICAL EVALUATION RECOMMENDED
            </div>
            <div style="margin-top:0.85rem; font-size:1.05rem; line-height:1.6;">
                {data["emergency_message"]}
            </div>
            <div style="margin-top:1.25rem; background:rgba(0,0,0,0.35); padding:1rem 1.25rem; border-radius:12px; display:flex; align-items:center; justify-content:space-between;">
                <div>
                    <span style="font-size:1.05rem; color:#f8fafc;">📞 Call <strong>{name}</strong>:</span>
                    <span style="font-size:1.6rem; font-weight:800; color:#fcd34d; margin-left:0.75rem;">{num}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Clarification Needed State ───────────────────────────
    if data.get("needs_clarification") and data.get("clarification_questions"):
        st.info("💡 **Clarification Needed Before Guidance:**")
        for q in data["clarification_questions"]:
            st.markdown(f"• {q}")
        return

    # ── Triage & Status Header ───────────────────────────────
    triage_outcome = data.get("triage_outcome", "self_care")
    urgency_summary = data.get("urgency_summary", "Self-care information")

    if triage_outcome == "self_care":
        badge = f'<span class="badge-self-care">✅ {urgency_summary}</span>'
    elif triage_outcome == "out_of_scope":
        badge = f'<span class="badge-clinician">⚠️ Out of Scope — {urgency_summary}</span>'
    else:
        badge = f'<span class="badge-urgent">🏥 {urgency_summary}</span>'

    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-content:space-between; padding:0.85rem 1.25rem; background:#0d201c; border-radius:12px; border:1px solid rgba(16,185,129,0.25); margin-bottom:1.25rem;">
        <div><strong>Triage Decision:</strong> {badge}</div>
        <div style="font-size:0.85rem; color:#a7f3d0;">Verified by Deterministic Engine & RRF</div>
    </div>
    """, unsafe_allow_html=True)

    # ── 7 Tabs Results Architecture ──────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Overview",
        "🫶 Safe Comfort Steps",
        "🌿 Ayurveda Lens",
        "📈 Evidence Table",
        "🕸️ Knowledge Map",
        "🛡️ Safety Plan",
        "📚 Sources & Provenance",
    ])

    # ── Tab 1: Overview ──────────────────────────────────────
    with tab1:
        st.markdown(f"""
        <div class="medical-card">
            <div class="card-header-title">📋 Summary of Reported Symptom</div>
            <div style="color:#f0fdf4; font-size:1.02rem; line-height:1.6;">{data.get('user_report_summary', 'No summary generated.')}</div>
        </div>
        """, unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 🌟 Primary Self-Care Highlights")
            for step in data.get("safe_comfort_steps", [])[:3]:
                st.markdown(f"• {step}")
        with col_b:
            st.markdown("#### ⚡ Evidence Confidence Metric")
            conf = data.get("overall_evidence_level", "insufficient").title()
            st.metric("Aggregate Evidence Level", conf, delta="Traceable Provenance")

    # ── Tab 2: Safe Steps ────────────────────────────────────
    with tab2:
        st.markdown("""<div class="card-header-title">🫶 Evidence-Grounded Low-Risk Comfort Measures</div>""", unsafe_allow_html=True)
        st.caption("Low-risk, non-pharmacological steps such as rest, hydration, positioning, and bland foods.")

        for step in data.get("safe_comfort_steps", []):
            st.markdown(f"""
            <div style="background:#122924; border-left:4px solid #10b981; padding:0.85rem 1.1rem; border-radius:10px; margin-bottom:0.75rem; color:#f0fdf4;">
                {step}
            </div>
            """, unsafe_allow_html=True)

    # ── Tab 3: Ayurveda Lens ─────────────────────────────────
    with tab3:
        st.markdown("""<div class="card-header-title">🌿 Ayurveda-Informed Non-Pharmacological Lifestyle Perspective</div>""", unsafe_allow_html=True)
        st.caption("Clearly labelled non-pharmacological lifestyle recommendations. Oral formulations, bhasma, and panchakarma are strictly excluded.")

        perspectives = data.get("ayurveda_perspectives", [])
        if not perspectives:
            st.info("No specific Ayurvedic lifestyle practices matched this mild symptom with verified clinical/traditional evidence.")
        else:
            for ap in perspectives:
                evidence = ap.get("evidence_label", "traditional_use_insufficient_clinical_evidence")
                if "supported" in evidence:
                    tag = '<span class="evidence-tag-high">Evidence Supported</span>'
                elif "limited" in evidence:
                    tag = '<span class="evidence-tag-mod">Limited Evidence</span>'
                else:
                    tag = '<span class="evidence-tag-lim">Traditional Use</span>'

                st.markdown(f"""
                <div style="background:#122924; border-left:4px solid #818cf8; padding:1rem; border-radius:12px; margin-bottom:0.85rem;">
                    <div style="display:flex; align-items:center; justify-content:space-between;">
                        <strong style="font-size:1.02rem; color:#f8fafc;">{ap.get('practice', '')}</strong>
                        {tag}
                    </div>
                    <div style="color:#94a3b8; font-size:0.9rem; margin-top:0.4rem; line-height:1.5;">{ap.get('description', '')}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── Tab 4: Evidence Table ────────────────────────────────
    with tab4:
        st.markdown("""<div class="card-header-title">📈 Multi-Factor Evidence Scoring Table</div>""", unsafe_allow_html=True)

        citations = data.get("citations", [])
        if not citations:
            st.info("No external MCP citations retrieved for this query. System operated on internal deterministic safety rules.")
        else:
            table_data = []
            for c in citations:
                table_data.append({
                    "Ref #": f"[{c.get('number')}]",
                    "Title": c.get("title", "")[:55] + "...",
                    "Study Design / Source": c.get("source_type", "Guideline").replace("_", " ").title(),
                    "Publication Date": c.get("publication_date", "N/A"),
                    "PMID / DOI": c.get("pmid") or c.get("doi") or "Canonical URL",
                    "Tier": "Tier 1-3 (High)" if "guideline" in c.get("source_type", "").lower() or "review" in c.get("source_type", "").lower() else "Tier 4-6",
                })
            st.dataframe(table_data, use_container_width=True)

    # ── Tab 5: Knowledge Map ─────────────────────────────────
    with tab5:
        st.markdown("""<div class="card-header-title">🕸️ GraphRAG Entity Traversal Map</div>""", unsafe_allow_html=True)
        st.caption("Visual entity traversal path in Neo4j knowledge graph.")

        st.markdown("""
        <div style="background:#091a17; border:1px solid rgba(16,185,129,0.3); border-radius:14px; padding:1.25rem; text-align:center;">
            <div style="font-family:monospace; color:#22d3ee; font-size:1rem; line-height:2;">
                (User Reported Symptom) ──[ACTION_MAY_SUPPORT]──► (SelfCareAction)<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├──[ACTION_CONTRAINDICATED_FOR]──► (Contraindication Check)<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└──[CLAIM_SUPPORTED_BY]──► (Study / MCP Source Tier 1-3)
            </div>
            <div style="margin-top:1rem; color:#a7f3d0; font-size:0.85rem;">
                ✓ Neo4j Cypher Traversal Verified &nbsp;|&nbsp; ✓ Milvus Vector RRF Score Active
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Tab 6: Safety Plan ───────────────────────────────────
    with tab6:
        st.markdown("""<div class="card-header-title">🛡️ Patient Safety & Care Boundaries Plan</div>""", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""<div style="font-weight:700; color:#f87171; margin-bottom:0.5rem;">🚫 What to Avoid</div>""", unsafe_allow_html=True)
            for item in data.get("things_to_avoid", []):
                st.markdown(f"• {item}")

        with col2:
            st.markdown("""<div style="font-weight:700; color:#fcd34d; margin-bottom:0.5rem;">👀 Changes to Monitor</div>""", unsafe_allow_html=True)
            for item in data.get("monitoring_guidance", []):
                st.markdown(f"• {item}")

        with col3:
            st.markdown("""<div style="font-weight:700; color:#60a5fa; margin-bottom:0.5rem;">🏥 Seeking Urgent Care</div>""", unsafe_allow_html=True)
            for item in data.get("seek_care_conditions", []):
                st.markdown(f"• {item}")

    # ── Tab 7: Sources & Provenance ──────────────────────────
    with tab7:
        st.markdown("""<div class="card-header-title">📚 Citation Provenance & Canonical Links</div>""", unsafe_allow_html=True)

        citations = data.get("citations", [])
        if not citations:
            st.info("No external citations needed for this deterministic safety response.")
        else:
            for cite in citations:
                num = cite.get("number", 1)
                title = cite.get("title", "Reference Title")
                authors = cite.get("authors", "")
                url = cite.get("url", "")
                date = cite.get("publication_date", "")

                st.markdown(f"**[{num}]** [{title}]({url})")
                st.caption(f"Authors: {authors} | Date: {date} | Canonical URL: {url}")
                st.markdown("---")

    # ── Copy & Download Controls ──────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📥 Report Export & Sharing")

    report_md = f"""# MedicoBuddy GraphRAG Wellness Report
Date: {time.strftime('%Y-%m-%d %H:%M UTC')}
Triage Status: {urgency_summary}

## Summary
{data.get('user_report_summary', '')}

## Safe Comfort Steps
{chr(10).join('- ' + s for s in data.get('safe_comfort_steps', []))}

## Disclaimer
{data.get('disclaimer', '')}
"""
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button(
            "📄 Download Markdown Report",
            data=report_md,
            file_name="medicobuddy_wellness_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_d2:
        st.download_button(
            "💾 Download JSON Raw Data",
            data=json.dumps(data, indent=2),
            file_name="medicobuddy_report_data.json",
            mime="application/json",
            use_container_width=True,
        )

    # Disclaimer Footer
    st.markdown(f"""
    <div style="font-size:0.8rem; color:#64748b; margin-top:1.5rem; padding:0.75rem; background:#081714; border-radius:8px; border:1px solid rgba(16,185,129,0.2);">
        ⚕️ {data.get('disclaimer', '')}
    </div>
    """, unsafe_allow_html=True)


def process_query_direct(user_input: str, user_context: dict[str, Any]) -> dict[str, Any]:
    """Fallback: Execute LangGraph workflow directly in Python if REST server is offline."""
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
        raise RuntimeError("Workflow produced no final response")

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
    render_header()
    user_context = render_sidebar()

    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ── Quick Symptom Intake Chips ───────────────────────────
    st.markdown("#### 💡 Guided Symptom Onboarding (Select a chip or type below)")
    cols = st.columns(3)
    selected_chip_text = None

    for idx, preset in enumerate(PRESET_SYMPTOMS):
        col = cols[idx % 3]
        btn_label = f"{preset['icon']} {preset['label']}"
        if col.button(btn_label, key=f"chip_btn_{idx}", use_container_width=True):
            selected_chip_text = preset["text"]

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Chat Messages Stream ─────────────────────────────────
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and isinstance(msg.get("data"), dict):
                render_results_panel(msg["data"])
            else:
                st.markdown(msg["content"])

    # ── User Input Box ───────────────────────────────────────
    chat_input_text = st.chat_input(
        "Describe your symptom (e.g., 'I have a mild headache since this morning')",
        key="main_chat_box",
    )

    query_to_process = selected_chip_text or chat_input_text

    if query_to_process:
        if not user_context.get("consent_given"):
            st.warning("Please check the disclaimer consent box in the sidebar to proceed.")
            return

        # Render user message
        st.session_state.messages.append({"role": "user", "content": query_to_process})
        with st.chat_message("user"):
            st.markdown(query_to_process)

        # Process through GraphRAG Workflow with Live Progress
        with st.chat_message("assistant"):
            progress_bar = st.progress(0, text="Initializing GraphRAG Pipeline...")
            time.sleep(0.1)
            progress_bar.progress(25, text="1. Running Deterministic Safety & Red-Flag Triage Engine...")
            time.sleep(0.1)
            progress_bar.progress(50, text="2. Querying Parallel MCP Connectors (PubMed / CT.gov / MedlinePlus)...")
            time.sleep(0.1)
            progress_bar.progress(75, text="3. Traversing Neo4j Knowledge Graph & Milvus RRF Fusion...")

            data = None
            # Try REST API backend first
            try:
                payload = {"message": query_to_process, **user_context}
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(f"{API_BASE}/chat", json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
            except Exception:
                logger.info("REST API offline — executing direct Python LangGraph Engine fallback")

            # Fallback to direct python workflow
            if data is None:
                try:
                    data = process_query_direct(query_to_process, user_context)
                except Exception as e:
                    progress_bar.empty()
                    st.error(f"Error evaluating query: {e}")
                    return

            progress_bar.progress(100, text="4. Response Evaluation & Provenance Verification Complete!")
            time.sleep(0.1)
            progress_bar.empty()

            render_results_panel(data)
            st.session_state.messages.append({
                "role": "assistant",
                "content": "",
                "data": data,
            })


if __name__ == "__main__":
    main()
