"""MedicoBuddy — Streamlit Frontend.

Accessible, production-ready chat interface for MedicoBuddy.
Supports both FastAPI REST backend connection and direct workflow fallback.
WCAG 2.2 AA compliance: contrast, keyboard navigation, screen reader labels.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
import streamlit as st

logger = logging.getLogger(__name__)

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="MedicoBuddy — GraphRAG AI Wellness Assistant",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ────────────────────────────────────────────────
API_BASE = os.getenv("API_BASE", "http://localhost:8000/api/v1")

# ── Custom CSS for Premium Design ────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    color: #f8fafc;
}

h1, h2, h3 { color: #f1f5f9 !important; }

.hero-title {
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #22d3ee, #6366f1, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0.2rem;
}

.hero-subtitle {
    color: #94a3b8;
    text-align: center;
    font-size: 1.05rem;
    margin-bottom: 1.5rem;
}

.emergency-banner {
    background: linear-gradient(135deg, #dc2626, #b91c1c);
    color: white;
    padding: 1.2rem;
    border-radius: 12px;
    margin: 1rem 0;
    font-weight: 600;
    border-left: 5px solid #fbbf24;
}

.section-header {
    color: #818cf8;
    font-weight: 600;
    font-size: 1.05rem;
    margin-top: 1rem;
    margin-bottom: 0.4rem;
}

.evidence-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 500;
}

.evidence-high { background: #065f46; color: #6ee7b7; }
.evidence-moderate { background: #713f12; color: #fcd34d; }
.evidence-limited { background: #7c2d12; color: #fdba74; }
.evidence-insufficient { background: #374151; color: #9ca3af; }

.disclaimer-box {
    background: rgba(51, 65, 85, 0.5);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 12px;
    padding: 1rem;
    color: #94a3b8;
    font-size: 0.85rem;
    margin-top: 1.5rem;
    line-height: 1.6;
}

div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e293b, #0f172a);
}
</style>
""", unsafe_allow_html=True)


def render_header() -> None:
    """Render the application header."""
    st.markdown('<div class="hero-title">🌿 MedicoBuddy</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">'
        'Evidence-Grounded GraphRAG AI Wellness Assistant · General Education & Self-Care Guidance'
        '</div>',
        unsafe_allow_html=True,
    )


def render_sidebar() -> dict[str, Any]:
    """Render the sidebar with user context form."""
    with st.sidebar:
        st.markdown("### 📋 User Profile & Context")
        st.markdown("*Provide context for personalized guidance*")

        age_range = st.selectbox(
            "Age Range",
            ["18_25", "26_35", "36_45", "46_55", "56_65", "under_18", "over_65", "unknown"],
            index=1,
            key="age_range_select",
            help="Select your age range for appropriate adult guidance",
        )

        pregnancy = st.selectbox(
            "Pregnancy Status",
            ["not_pregnant", "not_applicable", "pregnant", "breastfeeding", "unknown"],
            index=0,
            key="pregnancy_select",
        )

        is_immuno = st.checkbox(
            "Immunocompromised",
            value=False,
            key="immuno_check",
            help="Check if you have a weakened immune system",
        )

        conditions = st.text_input(
            "Chronic Conditions",
            placeholder="e.g. diabetes, hypertension (comma-separated)",
            key="conditions_input",
        )

        allergies = st.text_input(
            "Allergies",
            placeholder="e.g. peanuts, dairy (comma-separated)",
            key="allergies_input",
        )

        medications = st.text_input(
            "Current Medications",
            placeholder="e.g. metformin (comma-separated)",
            key="medications_input",
        )

        region = st.selectbox(
            "Region (for emergency contacts)",
            ["IN", "US", "UK", "EU"],
            index=0,
            key="region_select",
        )

        st.markdown("---")
        consent = st.checkbox(
            "I understand this is educational information, not medical advice",
            value=True,
            key="consent_check",
        )

        st.markdown("---")
        st.markdown(
            '<div class="disclaimer-box">'
            '⚕️ <strong>Important Notice:</strong> MedicoBuddy provides general wellness '
            'information only. It does not diagnose, prescribe, or replace '
            'professional medical advice.'
            '</div>',
            unsafe_allow_html=True,
        )

    return {
        "age_range": age_range,
        "pregnancy_status": pregnancy,
        "is_immunocompromised": is_immuno,
        "chronic_conditions": [c.strip() for c in conditions.split(",") if c.strip()],
        "allergies": [a.strip() for a in allergies.split(",") if a.strip()],
        "current_medications": [m.strip() for m in medications.split(",") if m.strip()],
        "region": region,
        "consent_given": consent,
    }


def render_response(data: dict[str, Any]) -> None:
    """Render the structured response."""
    # Emergency banner
    if data.get("emergency_message"):
        st.markdown(
            f'<div class="emergency-banner">🚨 {data["emergency_message"]}</div>',
            unsafe_allow_html=True,
        )
        if data.get("emergency_contact"):
            contact = data["emergency_contact"]
            st.error(f"📞 Call **{contact.get('name', '')}**: **{contact.get('number', '')}**")
        return

    # Clarification questions
    if data.get("needs_clarification") and data.get("clarification_questions"):
        st.info("I'd like to clarify a few details to provide accurate information:")
        for q in data["clarification_questions"]:
            st.markdown(f"• {q}")
        return

    # Urgency status
    urgency = data.get("urgency_summary", "")
    triage = data.get("triage_outcome", "")
    if triage == "urgent_care":
        st.error(f"⚠️ **{urgency}**")
    elif triage == "consult_clinician" or triage == "out_of_scope":
        st.warning(f"🏥 **{urgency}**")
    else:
        st.success(f"✅ **{urgency}**")

    # User report summary
    if data.get("user_report_summary"):
        st.markdown(f"**Summary:** {data['user_report_summary']}")

    # Safe comfort steps
    if data.get("safe_comfort_steps"):
        st.markdown('<div class="section-header">🫶 Low-Risk Comfort Measures</div>', unsafe_allow_html=True)
        for step in data["safe_comfort_steps"]:
            st.markdown(f"• {step}")

    # Ayurveda perspectives
    if data.get("ayurveda_perspectives"):
        st.markdown('<div class="section-header">🌿 Ayurveda-Informed Lifestyle Perspective</div>', unsafe_allow_html=True)
        for ap in data["ayurveda_perspectives"]:
            evidence = ap.get("evidence_label", "unknown")
            badge_class = {
                "evidence_supported": "evidence-high",
                "limited_or_preliminary_evidence": "evidence-moderate",
                "traditional_use_insufficient_clinical_evidence": "evidence-limited",
            }.get(evidence, "evidence-insufficient")
            st.markdown(
                f'**{ap.get("practice", "")}** '
                f'<span class="evidence-badge {badge_class}">{evidence.replace("_", " ").title()}</span>',
                unsafe_allow_html=True,
            )
            if ap.get("description"):
                st.markdown(f"  {ap.get('description', '')}")

    # What to avoid
    if data.get("things_to_avoid"):
        st.markdown('<div class="section-header">🚫 What to Avoid</div>', unsafe_allow_html=True)
        for item in data["things_to_avoid"]:
            st.markdown(f"• {item}")

    # Monitoring
    if data.get("monitoring_guidance"):
        st.markdown('<div class="section-header">👀 Changes to Monitor</div>', unsafe_allow_html=True)
        for item in data["monitoring_guidance"]:
            st.markdown(f"• {item}")

    # When to seek care
    if data.get("seek_care_conditions"):
        st.markdown('<div class="section-header">🏥 Seeking Professional Care</div>', unsafe_allow_html=True)
        for item in data["seek_care_conditions"]:
            st.markdown(f"• {item}")

    # Evidence level
    evidence = data.get("overall_evidence_level", "insufficient")
    badge = {
        "high": "evidence-high",
        "moderate": "evidence-moderate",
        "limited": "evidence-limited",
        "insufficient": "evidence-insufficient",
    }.get(evidence, "evidence-insufficient")
    st.markdown(
        f'**Evidence Confidence:** '
        f'<span class="evidence-badge {badge}">{evidence.title()}</span>',
        unsafe_allow_html=True,
    )

    # Citations
    if data.get("citations"):
        with st.expander("📚 Evidence Sources & Citations"):
            for cite in data["citations"]:
                link = cite.get("url", "")
                title = cite.get("title", "Untitled")
                num = cite.get("number", "")
                date = cite.get("publication_date", "")
                if link:
                    st.markdown(f"[{num}] [{title}]({link}) ({date})")
                else:
                    st.markdown(f"[{num}] {title} ({date})")

    # Disclaimer
    st.markdown(
        f'<div class="disclaimer-box">{data.get("disclaimer", "")}</div>',
        unsafe_allow_html=True,
    )


def process_query_direct(user_input: str, user_context: dict[str, Any]) -> dict[str, Any]:
    """Fallback: Execute LangGraph workflow directly in Python if API server is offline."""
    from medicobuddy.models.symptom import SymptomReport
    from medicobuddy.models.user_context import AgeRange, PregnancyStatus, UserContext
    from medicobuddy.workflow.graph import create_app

    app = create_app()

    try:
        age = AgeRange(user_context.get("age_range", "unknown"))
    except ValueError:
        age = AgeRange.UNKNOWN

    try:
        preg = PregnancyStatus(user_context.get("pregnancy_status", "unknown"))
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
        raise RuntimeError("Workflow generated no response")

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
    """Main Streamlit application."""
    render_header()
    user_context = render_sidebar()

    # Chat history state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and isinstance(msg.get("data"), dict):
                render_response(msg["data"])
            else:
                st.markdown(msg["content"])

    # User chat input
    user_input = st.chat_input(
        "Describe your symptom (e.g., 'I have a mild headache since this morning')",
        key="chat_input",
    )

    if user_input:
        if not user_context.get("consent_given"):
            st.warning("Please check the disclaimer consent box in the sidebar to proceed.")
            return

        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call API or Direct Fallback
        with st.chat_message("assistant"):
            with st.spinner("Analysing symptom and consulting evidence graph..."):
                data = None
                # Try REST API first
                try:
                    payload = {"message": user_input, **user_context}
                    with httpx.Client(timeout=30.0) as client:
                        resp = client.post(f"{API_BASE}/chat", json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                except Exception:
                    logger.info("FastAPI endpoint unavailable — using direct GraphRAG engine fallback")

                # If REST endpoint unavailable or errored, run direct engine
                if data is None:
                    try:
                        data = process_query_direct(user_input, user_context)
                    except Exception as e:
                        st.error(f"Error processing request: {e}")
                        return

                render_response(data)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "",
                    "data": data,
                })


if __name__ == "__main__":
    main()
