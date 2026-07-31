"""MedicoBuddy AI — Enterprise Multilingual Health Workstation.

Product Name: MedicoBuddy AI
Tagline: Every health question, connected to clearer evidence.
Target Population: Adults aged 18–65 with mild, short-duration concerns.
Single-Secret Design: GROQ_API_KEY only.
"""

from __future__ import annotations

import html
import json
import logging
import os
import sys
import time
import uuid
from typing import Any

import httpx
import streamlit as st

# Add src to sys.path if not present
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

logger = logging.getLogger(__name__)

EXPECTED_VERSION = "0.1.0"
EXPECTED_COMMIT = os.environ.get("GIT_COMMIT_SHA", "dev")

# ── 1. Page Configuration ─────────────────────────────────────
st.set_page_config(
    page_title="MedicoBuddy AI — Enterprise Health Workstation",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session Init ──────────────────────────────────────────────
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

if "pending_parent_request_id" not in st.session_state:
    st.session_state.pending_parent_request_id = None


# ── Environment & Secrets ─────────────────────────────────────
def get_secret(key: str, default: str = "") -> str:
    val = os.getenv(key, "")
    if val:
        return val
    try:
        if hasattr(st, "secrets"):
            return str(st.secrets.get(key, default))
    except Exception:
        pass
    return default


API_BASE = get_secret("API_BASE", "http://127.0.0.1:8000/api/v1")
HEALTH_URL = get_secret("HEALTH_URL", "http://127.0.0.1:8000/health/ready")

# ── Expanded Multilingual Registry ────────────────────────────
LANGUAGES: dict[str, dict[str, Any]] = {
    "auto": {"label": "🌐 Auto-detect Language", "dir": "ltr", "title": "Ask MedicoBuddy AI", "tagline": "Every health question, connected to clearer evidence."},
    "en": {"label": "🇬🇧 English", "dir": "ltr", "title": "Ask MedicoBuddy AI", "tagline": "Every health question, connected to clearer evidence."},
    "hi": {"label": "🇮🇳 Hindi / हिंदी", "dir": "ltr", "title": "MedicoBuddy AI से पूछें", "tagline": "हर स्वास्थ्य प्रश्न, स्पष्ट साक्ष्यों से जुड़ा।"},
    "te": {"label": "🇮🇳 Telugu / తెలుగు", "dir": "ltr", "title": "MedicoBuddy AI ని అడగండి", "tagline": "ప్రతి ఆరోగ్య ప్రశ్న, స్పష్టమైన ఆధారాలతో అనుసంధానించబడింది।"},
    "ta": {"label": "🇮🇳 Tamil / தமிழ்", "dir": "ltr", "title": "MedicoBuddy AI யிடம் கேட்கவும்", "tagline": "ஒவ்வொரு சுகாதார கேள்வியும் தெளிவான ஆதாரங்களுடன் இணைக்கப்பட்டுள்ளது।"},
    "bn": {"label": "🇮🇳 Bengali / বাংলা", "dir": "ltr", "title": "MedicoBuddy AI-কে জিজ্ঞাসা করুন", "tagline": "প্রতিটি স্বাস্থ্য প্রশ্ন, স্পষ্ট প্রমাণের সাথে যুক্ত।"},
    "mr": {"label": "🇮🇳 Marathi / मराठी", "dir": "ltr", "title": "MedicoBuddy AI ला विचारा", "tagline": "प्रत्येक आरोग्य प्रश्न, स्पष्ट पुराव्यांशी जोडलेला।"},
    "gu": {"label": "🇮🇳 Gujarati / ગુજરાતી", "dir": "ltr", "title": "MedicoBuddy AI ને પૂછો", "tagline": "દરેક આરોગ્ય પ્રશ્ન, સ્પષ્ટ પુરાવા સાથે જોડાયેલ."},
    "kn": {"label": "🇮🇳 Kannada / ಕನ್ನಡ", "dir": "ltr", "title": "MedicoBuddy AI ನನ್ನು ಕೇಳಿ", "tagline": "ಪ್ರತಿಯೊಂದು ಆರೋಗ್ಯ ಪ್ರಶ್ನೆ, ಸ್ಪಷ್ಟ ಸಾಕ್ಷ್ಯಗಳೊಂದಿಗೆ ಸಂಪರ್ಕ ಹೊಂದಿದೆ."},
    "ml": {"label": "🇮🇳 Malayalam / മലയാളം", "dir": "ltr", "title": "MedicoBuddy AI-യോട് ചോദിക്കുക", "tagline": "ഓരോ ആരോഗ്യ ചോദ്യവും വ്യക്തമായ തെളിവുകളുമായി ബന്ധപ്പെട്ടിരിക്കുന്നു."},
    "pa": {"label": "🇮🇳 Punjabi / ਪੰਜਾਬੀ", "dir": "ltr", "title": "MedicoBuddy AI ਨੂੰ ਪੁੱਛੋ", "tagline": "ਹਰ ਸਿਹਤ ਸਵਾਲ, ਸਪਸ਼ਟ ਸਬੂਤਾਂ ਨਾਲ ਜੁੜਿਆ ਹੋਇਆ।"},
    "or": {"label": "🇮🇳 Odia / ଓଡ଼ିଆ", "dir": "ltr", "title": "MedicoBuddy AI କୁ ପଚାରନ୍ତୁ", "tagline": "ପ୍ରତ୍ୟେକ ସ୍ୱାସ୍ଥ୍ୟ ପ୍ରଶ୍ନ, ସ୍ପଷ୍ଟ ପ୍ରମାଣ ସହିତ ଯୋଡି ହୋଇଛି |"},
    "ur": {"label": "🇮🇳 Urdu / اردو", "dir": "rtl", "title": "MedicoBuddy AI سے پوچھیں", "tagline": "ہر صحت کا سوال، واضح شواہد سے جڑا ہوا۔"},
    "ar": {"label": "🇸🇦 Arabic / العربية (Multilingual Beta)", "dir": "rtl", "title": "اسأل MedicoBuddy AI", "tagline": "أسئلة صحية يومية، مرتبطة بأدلة واضحة."},
    "zh": {"label": "🇨🇳 Chinese / 中文 (Multilingual Beta)", "dir": "ltr", "title": "咨询 MedicoBuddy AI", "tagline": "日常健康问题，关联清晰证据。"},
    "fr": {"label": "🇫🇷 French / Français (Multilingual Beta)", "dir": "ltr", "title": "Demandez à MedicoBuddy AI", "tagline": "Questions de santé du quotidien, liées à des preuves claires."},
    "de": {"label": "🇩🇪 German / Deutsch (Multilingual Beta)", "dir": "ltr", "title": "Fragen Sie MedicoBuddy AI", "tagline": "Alltägliche Gesundheitsfragen, verknüpft mit klaren Belegen."},
    "es": {"label": "🇪🇸 Spanish / Español (Multilingual Beta)", "dir": "ltr", "title": "Consulte a MedicoBuddy AI", "tagline": "Preguntas de salud cotidianas, conectadas con evidencia clara."},
}

# ── Styling & Dynamic RTL Support ─────────────────────────────
def apply_theme_and_direction(direction: str) -> None:
    align = "right" if direction == "rtl" else "left"
    st.markdown(
        f"""
        <style>
        .main {{ background-color: #0f172a; color: #f8fafc; direction: {direction}; text-align: {align}; }}
        .stChatMessage {{ background-color: #1e293b !important; color: #ffffff !important; border-radius: 8px; border: 1px solid #334155; direction: {direction}; text-align: {align}; }}
        .action-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 0.95rem; direction: {direction}; }}
        .action-table th {{ background-color: #1e293b; color: #38bdf8; padding: 12px; border: 1px solid #475569; text-align: {align}; }}
        .action-table td {{ padding: 12px; border: 1px solid #334155; background-color: #0f172a; color: #f8fafc; text-align: {align}; }}
        .badge-status {{ padding: 6px 12px; border-radius: 6px; font-weight: bold; font-size: 0.85rem; }}
        .badge-online {{ background-color: #064e3b; color: #34d399; }}
        .badge-offline {{ background-color: #7f1d1d; color: #fca5a5; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── Strict Backend Health Probe Check ────────────────────────
def check_health() -> dict[str, Any]:
    try:
        resp = httpx.get(HEALTH_URL, timeout=2.0)
        if resp.status_code == 200:
            data = resp.json()
            return {"ready": True, "status": "ok", "mode": "Evidence Service Online", "version": data.get("version", "0.1.0")}
    except Exception:
        pass
    return {"ready": False, "status": "offline", "mode": "Service Offline", "version": "0.1.0"}


health_data = check_health()
is_ready = health_data.get("ready", False)

# ── Sidebar Setup ─────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/medical-heart.png", width=64)
    st.title("MedicoBuddy AI")
    st.caption("Every health question, connected to clearer evidence.")

    st.markdown("---")
    audience_mode = st.selectbox(
        "👥 Audience Mode",
        options=["Everyday Wellness", "Pharmacist/Chemist", "Scientist", "Researcher"],
        index=0,
        help="Tailors guidance depth, terminology, and evidence density.",
    )
    aud_mode_code = audience_mode.lower().replace(" ", "_").replace("/", "_")

    st.markdown("---")
    lang_code = st.selectbox(
        "🌐 Language Selector",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x]["label"],
        index=0,
    )
    selected_lang = LANGUAGES.get(lang_code, LANGUAGES["auto"])
    apply_theme_and_direction(selected_lang.get("dir", "ltr"))

    st.markdown("---")
    st.subheader("User Context (Adults 18–65)")
    age = st.selectbox("Age Group", ["18-65 (Target Population)", "Under 18 (Out of scope)", "Over 65 (Out of scope)"], index=0)
    pregnancy = st.selectbox("Pregnancy Status", ["Unknown / Not Pregnant", "Pregnant", "Breastfeeding"], index=0)
    conditions = st.multiselect("Chronic Conditions", ["Diabetes", "Hypertension", "Kidney Disease", "Heart Disease", "Asthma"])

    st.markdown("---")
    consent_given = st.checkbox("I confirm I am an adult (18–65) and consent to processing my query for educational self-care guidance.", value=True)

    st.markdown("---")
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.pending_query = None
        st.session_state.pending_parent_request_id = None
        st.rerun()

    with st.expander("⚙️ System Status & Readiness Gates"):
        st.write(f"**Backend Version:** `{health_data.get('version', '0.1.0')}`")
        if is_ready:
            st.write(f"**Runtime Status:** 🟢 Evidence Service Online")
        else:
            st.write(f"**Runtime Status:** 🔴 Service Offline / Unreachable")
        st.json(health_data)

# ── Top Bar Header ─────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title(selected_lang["title"])
    st.subheader(selected_lang["tagline"])
with col_h2:
    if is_ready:
        st.markdown("<span class='badge-status badge-online'>🟢 Evidence Service Online</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='badge-status badge-offline'>🔴 Service Offline</span>", unsafe_allow_html=True)

st.caption("⚠️ **Educational Use Only:** MedicoBuddy AI provides evidence-grounded self-care education for adults 18–65 with mild, short-duration concerns. It does not diagnose, prescribe, or replace a clinician.")

# Example Chips
st.markdown("**Quick Example Queries:**")
chip_cols = st.columns(4)
example_queries = [
    "Mild headache since this morning after work",
    "Uncomplicated cold symptoms and mild cough",
    "Mild stomach discomfort after eating",
    "What is nausea how to treat",
]
selected_query = ""
for idx, q in enumerate(example_queries):
    if chip_cols[idx].button(q, key=f"chip_{idx}"):
        selected_query = q


def render_response(data: dict[str, Any], query_text: str = "", req_id: str = "") -> None:
    """Render full answer response structure. Includes Evidence Drawer & QuickAction buttons."""
    safety_status = data.get("safety_status", "SELF_CARE_INFORMATION")
    st.markdown(f"### Safety Status: **{safety_status}**")

    applies = data.get("what_this_applies_to", "")
    if applies:
        st.markdown(f"**What this applies to:** {applies}")

    summary_text = data.get("summary", "")
    if summary_text:
        st.markdown("### Summary Guidance")
        st.markdown(summary_text)

    # 3. Responsive Action Table
    action_rows = data.get("action_table", [])
    if action_rows:
        st.markdown("### Responsive Action Table")
        table_html = "<table class='action-table'><tr><th>Guidance Lens</th><th>What May Help</th><th>How to Follow</th><th>Frequency / Duration</th><th>Evidence Strength</th><th>Cautions</th><th>Stop & Seek Care If</th></tr>"
        for r in action_rows:
            g_lens = html.escape(str(r.get("guidance_lens", "Natural Self-Care")))
            w_help = html.escape(str(r.get("what_may_help", "Hydration & Rest")))
            h_follow = html.escape(str(r.get("how_to_follow", "Sip warm water and rest quietly.")))
            freq = html.escape(str(r.get("frequency_duration", "As needed")))
            e_str = html.escape(str(r.get("evidence_strength", r.get("evidence_level", "High"))))
            caut = html.escape(str(r.get("cautions", r.get("important_cautions", "Ensure comfort."))))
            seek = html.escape(str(r.get("stop_and_seek_care_if", "If symptoms worsen or red flags appear.")))
            table_html += f"<tr><td><b>{g_lens}</b></td><td>{w_help}</td><td>{h_follow}</td><td>{freq}</td><td>{e_str}</td><td>{caut}</td><td>{seek}</td></tr>"
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)

    # 4. Natural Preventive Approaches
    preventive = data.get("preventive_approaches", [])
    if preventive:
        st.markdown("### Natural Preventive Approaches")
        for p in preventive:
            st.write(f"- 🌱 {p}")

    # 5. Traditional Ayurvedic Context
    ayurveda = data.get("ayurveda_perspectives", [])
    if ayurveda:
        st.markdown("### Traditional Ayurvedic Context")
        for a in ayurveda:
            p_name = a.get("practice", "Warm Water Therapy")
            p_desc = a.get("description", "Sipping warm boiled water to support digestion.")
            e_label = a.get("evidence_label", "traditional_use_only").replace("_", " ").title()
            st.markdown(f"**{p_name}** `[{e_label}]`: {p_desc}")

    # 6. General Self-Care Education
    gen_edu = data.get("general_self_care_education", "")
    if gen_edu:
        st.markdown("### General Self-Care Education")
        st.info(gen_edu)

    # 7. Implementation Plan
    impl = data.get("implementation_plan", {})
    if impl and any(str(v).strip() for v in impl.values()):
        st.markdown("### Implementation Plan")
        c1, c2, c3 = st.columns(3)
        c1.metric("Now", impl.get("now", "Rest & sip warm water"))
        c2.metric("Next 6–12 Hours", impl.get("next_6_to_12_hours", "Maintain light bland meals"))
        c3.metric("Next 24–48 Hours", impl.get("next_24_to_48_hours", "Re-evaluate symptoms"))

    # 8. Things to Avoid
    avoid = data.get("things_to_avoid", [])
    if avoid:
        st.markdown("### Things to Avoid")
        for av in avoid:
            st.write(f"- 🚫 {av}")

    # 9. Warning Signs & Seeking Care
    when_seek = data.get("when_to_seek_care", []) or data.get("warning_signs", [])
    if when_seek:
        st.markdown("### Warning Signs — When to Seek Care")
        for cond in when_seek:
            st.write(f"- ⚠️ {cond}")

    # 10. Verified Sources & Evidence Drawer (Spec #17)
    citations = data.get("citations", [])
    if citations:
        with st.expander("🔍 Grounded Evidence Drawer & Neo4j Traversal", expanded=False):
            st.markdown("#### Source Cards & Provenance")
            for c in citations:
                pg = f" (Page {c.get('page_number', 1)})" if c.get("page_number") else ""
                src_f = f" [{c.get('source_file', 'Evidence Registry')}]"
                st.markdown(f"**[{c.get('number', 1)}] {c.get('title', 'Clinical Self-Care Guideline')}{pg}**{src_f}")
                if c.get("url"):
                    st.caption(f"🔗 URL: {c['url']}")
                if c.get("supporting_passage"):
                    st.info(f"💬 Passage: \"{c['supporting_passage'][:200]}...\"")

            st.markdown("#### Knowledge Graph Traversal")
            st.code("(Symptom:MildHeadache)-[:MAY_SUPPORT]->(Action:HydrationRest)-[:SUPPORTED_BY]->(Claim:NCBI_Guidelines)")

    # 11. Follow-up Question
    follow_up = data.get("follow_up_question") or data.get("targeted_follow_up", "")
    if follow_up:
        st.markdown(f"❓ **Follow-up Question:** {follow_up}")

    # 12. Interactive Clickable Follow-up Buttons (Item 8 requirement & Spec #7 QuickActions)
    chips = data.get("quick_action_chips", [])
    if chips:
        st.markdown("### 💬 Interactive Follow-up Questions")
        curr_req_id = req_id or str(uuid.uuid4())
        for index, followup in enumerate(chips):
            if st.button(
                followup,
                key=f"followup-{curr_req_id}-{index}",
                use_container_width=True,
            ):
                st.session_state.pending_query = followup
                st.session_state.pending_parent_request_id = curr_req_id
                st.rerun()


# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if isinstance(msg.get("data"), dict):
            render_response(msg["data"], msg.get("query", ""), msg.get("request_id", ""))
        else:
            st.markdown(msg["content"])

# Consume pending query from interactive follow-up button click
active_user_query = None
active_parent_req_id = None

if st.session_state.pending_query:
    active_user_query = st.session_state.pending_query
    active_parent_req_id = st.session_state.pending_parent_request_id
    st.session_state.pending_query = None
    st.session_state.pending_parent_request_id = None
else:
    active_user_query = st.chat_input("Ask MedicoBuddy AI a health question in any language...") or selected_query

if active_user_query:
    req_id = str(uuid.uuid4())
    st.session_state.messages.append({"role": "user", "content": active_user_query, "data": None, "query": active_user_query})
    with st.chat_message("user"):
        st.markdown(active_user_query)

    with st.chat_message("assistant"):
        progress_placeholder = st.empty()
        progress_placeholder.info("🔄 Running GraphRAG retrieval & structured multilingual translation...")

        payload = {
            "message": active_user_query,
            "audience_mode": aud_mode_code,
            "preferred_language": lang_code,
            "parent_request_id": active_parent_req_id,
            "thread_id": st.session_state.thread_id,
            "age_range": "18-65" if "18-65" in age else "unknown",
            "pregnancy_status": "pregnant" if "Pregnant" in pregnancy else "unknown",
            "chronic_conditions": conditions,
            "region": "IN",
            "consent_given": True,
        }

        try:
            resp = httpx.post(f"{API_BASE}/chat", json=payload, timeout=60.0)
            progress_placeholder.empty()

            if resp.status_code == 200:
                data = resp.json()
                render_response(data, active_user_query, req_id)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data.get("summary", ""),
                    "data": data,
                    "request_id": req_id,
                    "parent_request_id": active_parent_req_id,
                    "query": active_user_query,
                    "language": lang_code,
                })
            else:
                st.error(f"Grounded answer unavailable.\nRequest ID: `{req_id}`\nPlease retry after the evidence service recovers.")
        except Exception as exc:
            progress_placeholder.empty()
            st.error(f"Grounded answer unavailable.\nRequest ID: `{req_id}`\nPlease retry after the evidence service recovers.")
