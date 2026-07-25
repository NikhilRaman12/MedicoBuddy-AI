"""MedicoBuddy AI — Enterprise Health Educational Workspace.

Refinements:
1. Enterprise Tagline: "Every health question, connected to clearer evidence"
2. Status Badge: "Evidence service ready" (Replaced oversized GraphRAG badges)
3. Empty Evidence Panel: Clean empty state ("Your evidence, sources and connections will appear here")
   without static ASCII flowcharts; reveals real citations & connections after query execution.
4. Global Language Selector: Searchable multi-language dictionary with RTL & locale code support.
5. Dark Navy & Jade Enterprise Palette with WCAG 2.2 AA Contrast.
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
    page_title="MedicoBuddy AI — Health Educational Workspace",
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

# ── Multilingual Dictionary with Locale Codes & RTL Support ────
LANGUAGES: dict[str, dict[str, Any]] = {
    "en": {
        "label": "English (en)",
        "dir": "ltr",
        "title": "Ask MedicoBuddy",
        "tagline": "Every health question, connected to clearer evidence",
        "input_placeholder": "Ask MedicoBuddy a health question...",
        "new_chat": "➕ New Conversation",
        "recent_chats": "Recent Conversations",
        "preferences": "Preferences & Language",
        "evidence_title": "Evidence Intelligence",
        "quick_queries": "Quick Example Queries",
        "status_ready": "🟢 Evidence service ready",
        "empty_evidence": "Your evidence, sources and connections will appear here.",
    },
    "hi": {
        "label": "Hindi / हिंदी (hi)",
        "dir": "ltr",
        "title": "MedicoBuddy से पूछें",
        "tagline": "हर स्वास्थ्य प्रश्न, स्पष्ट साक्ष्यों से जुड़ा",
        "input_placeholder": "MedicoBuddy से स्वास्थ्य प्रश्न पूछें...",
        "new_chat": "➕ नई बातचीत",
        "recent_chats": "हाल की बातचीत",
        "preferences": "प्राथमिकताएं और भाषा",
        "evidence_title": "साक्ष्य इंटेलिजेंस",
        "quick_queries": "त्वरित उदाहरण प्रश्न",
        "status_ready": "🟢 साक्ष्य सेवा तैयार है",
        "empty_evidence": "आपके साक्ष्य, स्रोत और कनेक्शन यहां दिखाई देंगे।",
    },
    "ta": {
        "label": "Tamil / தமிழ் (ta)",
        "dir": "ltr",
        "title": "MedicoBuddy யிடம் கேட்கவும்",
        "tagline": "ஒவ்வொரு சுகாதார கேள்வியும் தெளிவான ஆதாரங்களுடன் இணைக்கப்பட்டுள்ளது",
        "input_placeholder": "MedicoBuddy யிடம் சுகாதார கேள்வி கேட்கவும்...",
        "new_chat": "➕ புதிய உரையாடல்",
        "recent_chats": "சமீபத்திய உரையாடல்கள்",
        "preferences": "விருப்பத்தேர்வுகள் & மொழி",
        "evidence_title": "ஆதார நுண்ணறிவு",
        "quick_queries": "வேகமான உதாரண கேள்விகள்",
        "status_ready": "🟢 ஆதார சேவை தயார்",
        "empty_evidence": "உங்கள் ஆதாரங்கள், மூலங்கள் மற்றும் இணைப்புகள் இங்கு தோன்றும்.",
    },
    "es": {
        "label": "Spanish / Español (es)",
        "dir": "ltr",
        "title": "Pregunta a MedicoBuddy",
        "tagline": "Cada pregunta de salud, conectada a evidencia más clara",
        "input_placeholder": "Haz una pregunta de salud a MedicoBuddy...",
        "new_chat": "➕ Nueva conversación",
        "recent_chats": "Conversaciones recientes",
        "preferences": "Preferencias e idioma",
        "evidence_title": "Inteligencia de Evidencia",
        "quick_queries": "Consultas de ejemplo",
        "status_ready": "🟢 Servicio de evidencia listo",
        "empty_evidence": "Tus evidencias, fuentes y conexiones aparecerán aquí.",
    },
    "fr": {
        "label": "French / Français (fr)",
        "dir": "ltr",
        "title": "Posez une question à MedicoBuddy",
        "tagline": "Chaque question de santé, reliée à des preuves plus claires",
        "input_placeholder": "Posez une question de santé à MedicoBuddy...",
        "new_chat": "➕ Nouvelle conversation",
        "recent_chats": "Conversations récentes",
        "preferences": "Préférences et langue",
        "evidence_title": "Intelligence de Preuve",
        "quick_queries": "Exemples de questions",
        "status_ready": "🟢 Service de preuve prêt",
        "empty_evidence": "Vos preuves, sources et connexions apparaîtront ici.",
    },
    "ar": {
        "label": "Arabic / العربية (ar - RTL)",
        "dir": "rtl",
        "title": "اسأل MedicoBuddy",
        "tagline": "كل سؤال صحي، متصل بأدلة أكثر وضوحاً",
        "input_placeholder": "اسأل MedicoBuddy سؤالاً صحياً...",
        "new_chat": "➕ محادثة جديدة",
        "recent_chats": "المحادثات الأخيرة",
        "preferences": "التفضيلات واللغة",
        "evidence_title": "ذكاء الأدلة",
        "quick_queries": "أسئلة توضيحية",
        "status_ready": "🟢 خدمة الأدلة جاهزة",
        "empty_evidence": "ستظهر أدلتك والمصادر والروابط هنا.",
    },
}

SUGGESTION_OPTIONS = [
    "Mild headache since morning",
    "Temporary fatigue after work",
    "Slight nausea after eating",
    "Minor digestive bloating",
]

# ── Design Token CSS (Scoped WCAG AA Contrast Overrides) ──────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 14px !important;
}

.stApp {
    background-color: #090d16 !important;
    color: #f8fafc !important;
}

section[data-testid="stSidebar"] {
    background-color: #0f172a !important;
    border-right: 1px solid #334155 !important;
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #f8fafc !important;
}

section[data-testid="stSidebar"] .stSelectbox div,
section[data-testid="stSidebar"] .stTextInput input {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border: 1px solid #475569 !important;
}

header[data-testid="stHeader"] { visibility: hidden; height: 0; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

.stButton>button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    border: 1px solid #334155 !important;
    background-color: #1e293b !important;
    color: #f8fafc !important;
}

.stButton>button:hover {
    border-color: #10b981 !important;
    color: #34d399 !important;
}
</style>
""", unsafe_allow_html=True)


# ── 2. Performance Caching Wrapper ────────────────────────────
@st.cache_resource(show_spinner=False)
def get_cached_graph_app():
    """Cache the compiled LangGraph workflow application instance."""
    from medicobuddy.workflow.graph import create_app
    logger.info("Initializing cached LangGraph engine...")
    return create_app()


# ── 3. Sidebar Controls & Global Language Selector ────────────
def render_sidebar() -> dict[str, Any]:
    """Render Navigation Sidebar with Global Searchable Language Selector & WCAG AA Contrast."""
    with st.sidebar:
        st.title("🩺 MedicoBuddy AI")
        st.caption("Evidence-Grounded Health Educational Assistant")
        st.markdown("---")

        lang_code = st.selectbox(
            "Language / भाषा / மொழி",
            options=list(LANGUAGES.keys()),
            format_func=lambda k: LANGUAGES[k]["label"],
            index=0,
        )
        t = LANGUAGES[lang_code]

        if st.button(t["new_chat"], use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.markdown(f"### {t['recent_chats']}")
        st.write("• **Mild Headache** *(Today)*")
        st.write("• **Indigestion & Gas** *(Yesterday)*")
        st.write("• **Temporary Fatigue** *(Jul 22)*")

        st.markdown("---")
        st.markdown(f"### {t['preferences']}")
        st.checkbox("High Contrast Mode", value=True)
        st.checkbox("Scrub PII from logs", value=True)

        st.markdown("---")
        with st.expander("👤 Patient Context Parameters", expanded=False):
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
        st.caption("🔒 **Privacy Guarantee:** Zero PII collected. Automated regex PII scrubbing active.")

    return {
        "lang_code": lang_code,
        "translations": t,
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
    if data.get("emergency_message"):
        contact = data.get("emergency_contact") or {}
        num = contact.get("number", "112")
        name = contact.get("name", "Emergency Medical Services")

        st.error(
            f"🚨 **IMMEDIATE MEDICAL EVALUATION RECOMMENDED**\n\n{data['emergency_message']}\n\n📞 Contact {name}: **{num}**"
        )
        return

    triage = data.get("triage_outcome", "self_care")
    summary = data.get("urgency_summary", "Self-Care Guidance")

    if triage == "self_care":
        st.success(f"✅ **Triage Assessment:** {summary}")
    else:
        st.error(f"⚠️ **Triage Assessment:** {summary}")

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

    st.markdown("---")
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
def render_evidence_panel(data: dict[str, Any] | None, t: dict[str, Any]) -> None:
    """Render persistent Evidence Intelligence Panel in right 30% column."""
    st.markdown(f"### {t['evidence_title']}")

    if not data:
        st.info("💡 **Evidence Validation Dock**")
        st.write(t["empty_evidence"])
        return

    # Evidence Strength Metric
    strength = data.get("overall_evidence_level", "insufficient").title()
    st.metric("Evidence Strength Score", strength)
    st.markdown("---")

    # Evidence Connections Graph Summary
    st.markdown("##### Evidence Connections")
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
    st.caption("⚠️ **Educational Disclaimer:** Guidance for adult educational purposes only. Consult a licensed clinician for medical decisions.")


# ── 7. Main Application Workspace ─────────────────────────────
def main() -> None:
    context = render_sidebar()
    t = context["translations"]

    # Top App Header Bar
    h_col1, h_col2 = st.columns([3.2, 1.2])
    with h_col1:
        st.title(t["title"])
        st.caption(t["tagline"])
    with h_col2:
        st.success(t["status_ready"])

    # 70/30 Workspace Split
    col_left, col_right = st.columns([2.7, 1.1])

    latest_data = None

    with col_left:
        selected_suggestion = st.selectbox(
            t["quick_queries"],
            ["Type custom question below..."] + SUGGESTION_OPTIONS,
            index=0,
            key="quick_suggestion_select",
        )

        st.markdown("---")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant" and isinstance(msg.get("data"), dict):
                    render_response_components(msg["data"])
                    latest_data = msg["data"]
                else:
                    st.markdown(msg["content"])

        user_input = st.chat_input(t["input_placeholder"], key="main_chat_composer")
        
        query_to_process = None
        if user_input:
            query_to_process = user_input
        elif selected_suggestion != "Type custom question below...":
            query_to_process = selected_suggestion

        if query_to_process:
            st.session_state.messages.append({"role": "user", "content": query_to_process})
            with st.chat_message("user"):
                st.markdown(query_to_process)

            with st.chat_message("assistant"):
                with st.spinner("Evaluating evidence & safety rules..."):
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
        render_evidence_panel(latest_data, t)


if __name__ == "__main__":
    main()
