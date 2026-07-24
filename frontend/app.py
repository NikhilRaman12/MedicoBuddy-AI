"""MedicoBuddy — Streamlit Frontend.

Accessible chat interface for the MedicoBuddy wellness assistant.
WCAG 2.2 AA compliance: contrast, keyboard navigation, screen reader labels.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import streamlit as st

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="MedicoBuddy — Wellness Assistant",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ────────────────────────────────────────────────
API_BASE = "http://localhost:8000/api/v1"

# ── Custom CSS for Premium Design ────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

.main { background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%); }

.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
}

h1, h2, h3 { color: #f1f5f9 !important; }

.hero-title {
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #22d3ee, #6366f1, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0.5rem;
}

.hero-subtitle {
    color: #94a3b8;
    text-align: center;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

.emergency-banner {
    background: linear-gradient(135deg, #dc2626, #b91c1c);
    color: white;
    padding: 1.2rem;
    border-radius: 12px;
    margin: 1rem 0;
    font-weight: 600;
    border-left: 5px solid #fbbf24;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.4); }
    50% { box-shadow: 0 0 0 10px rgba(220, 38, 38, 0); }
}

.response-card {
    background: rgba(30, 41, 59, 0.8);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
    transition: transform 0.2s ease;
}

.response-card:hover { transform: translateY(-2px); }

.section-header {
    color: #818cf8;
    font-weight: 600;
    font-size: 1rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
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

.sidebar .stRadio label { color: #e2e8f0 !important; }

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
        'Evidence-grounded wellness guidance · Not a substitute for medical advice'
        '</div>',
        unsafe_allow_html=True,
    )


def render_sidebar() -> dict[str, Any]:
    """Render the sidebar with user context form."""
    with st.sidebar:
        st.markdown("### 📋 Your Context")
        st.markdown("*Provide optional context for personalised guidance*")

        age_range = st.selectbox(
            "Age Range",
            ["unknown", "18_25", "26_35", "36_45", "46_55", "56_65", "under_18", "over_65"],
            index=0,
            key="age_range_select",
            help="Select your age range for appropriate guidance",
        )

        pregnancy = st.selectbox(
            "Pregnancy Status",
            ["not_applicable", "not_pregnant", "pregnant", "breastfeeding", "unknown"],
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
            value=False,
            key="consent_check",
        )

        st.markdown("---")
        st.markdown(
            '<div class="disclaimer-box">'
            '⚕️ <strong>Important:</strong> MedicoBuddy provides general wellness '
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
        st.info("I'd like to understand your situation better:")
        for q in data["clarification_questions"]:
            st.markdown(f"• {q}")
        return

    # Urgency status
    urgency = data.get("urgency_summary", "")
    triage = data.get("triage_outcome", "")
    if triage == "urgent_care":
        st.error(f"⚠️ **{urgency}**")
    elif triage == "consult_clinician":
        st.warning(f"🏥 **{urgency}**")
    else:
        st.success(f"✅ **{urgency}**")

    # User report summary
    if data.get("user_report_summary"):
        st.markdown(f"**Summary:** {data['user_report_summary']}")

    # Safe comfort steps
    if data.get("safe_comfort_steps"):
        st.markdown('<div class="section-header">🫶 Steps That May Provide Comfort</div>', unsafe_allow_html=True)
        for step in data["safe_comfort_steps"]:
            st.markdown(f"• {step}")

    # Ayurveda perspectives
    if data.get("ayurveda_perspectives"):
        st.markdown('<div class="section-header">🌿 Ayurveda-Informed Perspective</div>', unsafe_allow_html=True)
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
            st.markdown(f"  {ap.get('description', '')}")

    # What to avoid
    if data.get("things_to_avoid"):
        st.markdown('<div class="section-header">🚫 What to Avoid</div>', unsafe_allow_html=True)
        for item in data["things_to_avoid"]:
            st.markdown(f"• {item}")

    # Monitoring
    if data.get("monitoring_guidance"):
        st.markdown('<div class="section-header">👀 What to Monitor</div>', unsafe_allow_html=True)
        for item in data["monitoring_guidance"]:
            st.markdown(f"• {item}")

    # When to seek care
    if data.get("seek_care_conditions"):
        st.markdown('<div class="section-header">🏥 Seek Professional Care If</div>', unsafe_allow_html=True)
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
        with st.expander("📚 Citations & Sources"):
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


def main() -> None:
    """Main Streamlit application."""
    render_header()
    user_context = render_sidebar()

    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and isinstance(msg.get("data"), dict):
                render_response(msg["data"])
            else:
                st.markdown(msg["content"])

    # User input
    user_input = st.chat_input(
        "Describe your symptom (e.g., 'I have a mild headache since this morning')",
        key="chat_input",
    )

    if user_input:
        if not user_context.get("consent_given"):
            st.warning("Please acknowledge the disclaimer in the sidebar before proceeding.")
            return

        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call API
        with st.chat_message("assistant"):
            with st.spinner("Analysing your concern..."):
                try:
                    payload = {
                        "message": user_input,
                        **user_context,
                    }
                    with httpx.Client(timeout=60.0) as client:
                        resp = client.post(f"{API_BASE}/chat", json=payload)
                        resp.raise_for_status()
                        data = resp.json()

                    render_response(data)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "",
                        "data": data,
                    })

                except httpx.ConnectError:
                    st.error(
                        "Cannot connect to the MedicoBuddy API. "
                        "Please ensure the backend is running on port 8000."
                    )
                except Exception as e:
                    st.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
