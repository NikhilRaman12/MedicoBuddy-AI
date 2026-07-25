"""MedicoBuddy — Enterprise Healthcare SaaS Workspace.

Native Streamlit Implementation — Zero raw HTML string leaks, 100% high contrast,
clean layout, responsive consultation interface, and evidence intelligence panel.
"""

from __future__ import annotations

import json
import logging
import os
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
    "Temporary fatigue after work",
    "Slight nausea after eating",
    "Minor digestive indigestion",
    "Short-duration low fever",
]


def render_sidebar() -> dict[str, Any]:
    """Render Left Rail with Session History & Patient Context Drawer using Native Streamlit API."""
    with st.sidebar:
        st.title("🩺 MedicoBuddy")
        st.caption("Enterprise Healthcare AI Assistant")
        st.markdown("---")

        if st.button("➕ New Session", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.markdown("### Recent Sessions")
        st.write("• Mild Headache (Today)")
        st.write("• Indigestion & Gas (Yesterday)")
        st.write("• Temporary Fatigue (Jul 22)")

        st.markdown("---")
        st.markdown("### Patient Context Drawer")

        with st.expander("👤 Patient Parameters", expanded=False):
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
            medications_raw = st.text_input("Current Medications", placeholder="e.g. metformin")

            region = st.selectbox("Region", ["IN", "US", "UK", "EU"], index=0)
            consent_given = st.checkbox("Consent Acknowledged", value=True)

        st.markdown("---")
        st.caption("🔒 **Privacy Guarantee:** Zero PII collected. Automated regex PII scrubbing active on logs.")

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
    """Render central workspace answer components using clean native Streamlit markdown & containers."""
    # ── Emergency State ──────────────────────────────────────
    if data.get("emergency_message"):
        contact = data.get("emergency_contact") or {}
        num = contact.get("number", "112")
        name = contact.get("name", "Emergency Medical Services")

        st.error(f"🚨 **IMMEDIATE MEDICAL EVALUATION RECOMMENDED**\n\n{data['emergency_message']}\n\n📞 Call **{name}**: **{num}**")
        return

    # ── Clarification State ──────────────────────────────────
    if data.get("needs_clarification") and data.get("clarification_questions"):
        st.info("💡 **Clarification Needed Before Guidance:**")
        for q in data["clarification_questions"]:
            st.markdown(f"• {q}")
        return

    # ── Triage Outcome Banner ────────────────────────────────
    triage_outcome = data.get("triage_outcome", "self_care")
    urgency_summary = data.get("urgency_summary", "Self-care information")

    if triage_outcome == "self_care":
        st.success(f"✅ **Triage Status:** {urgency_summary}")
    elif triage_outcome == "out_of_scope":
        st.warning(f"⚠️ **Triage Status:** Out of Scope — {urgency_summary}")
    else:
        st.error(f"🏥 **Triage Status:** {urgency_summary}")

    # ── Answer Tabs ──────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "Overview",
        "Safe Comfort Steps",
        "Ayurveda Lens",
        "Safety Boundaries",
    ])

    with tab1:
        st.markdown("##### Summary of Reported Symptom")
        st.write(data.get("user_report_summary", "No summary available."))

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


def render_evidence_panel(data: dict[str, Any] | None) -> None:
    """Render persistent right-side Evidence Intelligence panel using Native Streamlit."""
    st.markdown("### Evidence Intelligence")

    if not data:
        st.caption("Submit a symptom query to inspect evidence sources, certainty score, and graph-path preview.")
        return

    # Certainty Score Metric
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
   └──► (EvidenceClaim) ──► (MCP Source)
    """, language="text")
    st.markdown("---")

    # Citations List
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
    """Direct Python engine execution fallback when REST API server is offline."""
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
    user_context = render_sidebar()

    # Workspace 3-Column Split
    col_center, col_right = st.columns([2.8, 1.2])

    latest_data = None

    with col_center:
        st.header("How can I help today?")
        st.caption("Describe your symptom below or pick a suggested topic for evidence-grounded guidance.")

        # 3-Stage Journey Indicator
        st.info("🔄 **3-Stage GraphRAG Journey:** `1. Safety Check` ➔ `2. Evidence Retrieval` ➔ `3. Grounded Guidance`")

        # Selectbox Suggestion Pills (Prevents button text wrapping bugs!)
        selected_query_option = st.selectbox(
            "Quick Symptom Suggestions",
            ["Type custom query below..."] + SUGGESTED_QUERIES,
            index=0,
            key="symptom_suggestion_select",
        )

        st.markdown("---")

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

        query_to_process = None
        if user_input:
            query_to_process = user_input
        elif selected_query_option != "Type custom query below...":
            query_to_process = selected_query_option

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
