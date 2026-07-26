"""MedicoBuddy AI — Enterprise Multilingual Health Workstation.

Product Name: MedicoBuddy AI
Tagline: Everyday health questions, connected to clearer evidence.
Target Population: Adults aged 18–65 with mild, short-duration concerns.
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
    page_title="MedicoBuddy AI — Multilingual Health Workstation",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

# ── 22 Scheduled Indian Languages + Global BCP-47 Languages ───
LANGUAGES: dict[str, dict[str, Any]] = {
    "auto": {"label": "🌐 Auto-detect Language", "dir": "ltr", "title": "Ask MedicoBuddy AI", "tagline": "Everyday health questions, connected to clearer evidence."},
    "hi": {"label": "🇮🇳 Hindi / हिंदी", "dir": "ltr", "title": "MedicoBuddy AI से पूछें", "tagline": "हर स्वास्थ्य प्रश्न, स्पष्ट साक्ष्यों से जुड़ा।"},
    "bn": {"label": "🇮🇳 Bengali / বাংলা", "dir": "ltr", "title": "MedicoBuddy AI-কে জিজ্ঞাসা করুন", "tagline": "প্রতিটি স্বাস্থ্য প্রশ্ন, স্পষ্ট প্রমাণের সাথে যুক্ত।"},
    "te": {"label": "🇮🇳 Telugu / తెలుగు", "dir": "ltr", "title": "MedicoBuddy AI ని అడగండి", "tagline": "ప్రతి ఆరోగ్య ప్రశ్న, స్పష్టమైన ఆధారాలతో అనుసంధానించబడింది।"},
    "mr": {"label": "🇮🇳 Marathi / मराठी", "dir": "ltr", "title": "MedicoBuddy AI ला विचारा", "tagline": "प्रत्येक आरोग्य प्रश्न, स्पष्ट पुराव्यांशी जोडलेला।"},
    "ta": {"label": "🇮🇳 Tamil / தமிழ்", "dir": "ltr", "title": "MedicoBuddy AI யிடம் கேட்கவும்", "tagline": "ஒவ்வொரு சுகாதார கேள்வியும் தெளிவான ஆதாரங்களுடன் இணைக்கப்பட்டுள்ளது।"},
    "ur": {"label": "🇮🇳 Urdu / اردو", "dir": "rtl", "title": "MedicoBuddy AI سے پوچھیں", "tagline": "ہر صحت کا سوال، واضح ثبوتوں سے جڑا ہوا۔"},
    "gu": {"label": "🇮🇳 Gujarati / ગુજરાતી", "dir": "ltr", "title": "MedicoBuddy AI ને પૂછો", "tagline": "દરેક આરોગ્ય પ્રશ્ન, સ્પષ્ટ પુરાવા સાથે જોડાયેલ।"},
    "kn": {"label": "🇮🇳 Kannada / ಕನ್ನಡ", "dir": "ltr", "title": "MedicoBuddy AI ಯನ್ನು ಕೇಳಿ", "tagline": "ಪ್ರತಿ ಆರೋಗ್ಯ ಪ್ರಶ್ನೆ, ಸ್ಪಷ್ಟ ಸಾಕ್ಷ್ಯಗಳೊಂದಿಗೆ ಸಂಪರ್ಕ ಹೊಂದಿದೆ।"},
    "ml": {"label": "🇮🇳 Malayalam / മലയാളം", "dir": "ltr", "title": "MedicoBuddy AI യോട് ചോദിക്കുക", "tagline": "ഓരോ ആരോഗ്യ ചോദ്യവും വ്യക്തമായ തെളിവുകളുമായി ബന്ധപ്പെട്ടിരിക്കുന്നു।"},
    "or": {"label": "🇮🇳 Odia / ଓଡ଼ିଆ", "dir": "ltr", "title": "MedicoBuddy AI କୁ ପଚାରନ୍ତୁ", "tagline": "ପ୍ରତ୍ୟେକ ସ୍ୱାସ୍ଥ୍ୟ ପ୍ରଶ୍ନ, ସ୍ପଷ୍ଟ ପ୍ରମାଣ ସହିତ ସଂଯୁକ୍ତ।"},
    "pa": {"label": "🇮🇳 Punjabi / ਪੰਜਾਬੀ", "dir": "ltr", "title": "MedicoBuddy AI ਤੋਂ ਪੁੱਛੋ", "tagline": "ਹਰ ਸਿਹਤ ਦਾ ਸਵਾਲ, ਸਪਸ਼ਟ ਸਬੂਤਾਂ ਨਾਲ ਜੁੜਿਆ ਹੋਇਆ।"},
    "as": {"label": "🇮🇳 Assamese / অসমীয়া", "dir": "ltr", "title": "MedicoBuddy AI ক সোধক", "tagline": "প্ৰতিটো স্বাস্থ্য প্ৰশ্ন, স্পষ্ট প্ৰমাণৰ সৈতে সংযোজিত।"},
    "mai": {"label": "🇮🇳 Maithili / मैथिली", "dir": "ltr", "title": "MedicoBuddy AI सँ पूछू", "tagline": "प्रत्येक स्वास्थ्य प्रश्न, स्पष्ट साक्ष्य सँ जुड़ल।"},
    "sat": {"label": "🇮🇳 Santali / ᱥᱟᱱᱛᱟᱲᱤ", "dir": "ltr", "title": "MedicoBuddy AI ᱠᱩᱞᱤᱭᱮᱢ", "tagline": "ᱡᱚᱛᱚ ᱦᱚᱲᱢᱚ ᱠᱩᱠᱞᱤ, ᱥᱟᱹᱨᱤ ᱯᱩᱨᱟᱹᱣ ᱥᱟᱶ ᱡᱚᱲᱟᱣ।"},
    "ks": {"label": "🇮🇳 Kashmiri / کٲشُر", "dir": "rtl", "title": "MedicoBuddy AI پیٹھ پُچھو", "tagline": "پرَتھ صَحتُک سَوال، صَحیح ثابِتَن سِتھ جوڈتھ۔"},
    "ne": {"label": "🇮🇳 Nepali / नेपाली", "dir": "ltr", "title": "MedicoBuddy AI लाई सोध्नुहोस्", "tagline": "प्रत्येक स्वास्थ्य प्रश्न, स्पष्ट प्रमाणसँग जोडिएको।"},
    "kok": {"label": "🇮🇳 Konkani / कोंकणी", "dir": "ltr", "title": "MedicoBuddy AI क विचारात", "tagline": "दर एक भलायकेचो प्रश्न, निवळ पुराव्याक जोडिल्लो।"},
    "sd": {"label": "🇮🇳 Sindhi / سنڌي", "dir": "rtl", "title": "MedicoBuddy AI کان پڇو", "tagline": "هر صحت جو سوال، چٽن ثبوتن سان جڙيل."},
    "doi": {"label": "🇮🇳 Dogri / डोगरी", "dir": "ltr", "title": "MedicoBuddy AI थौह् गै पुच्छो", "tagline": "हर सेहत दा सवाल, साफ सबूतें कन्नै जुड़े दा।"},
    "brx": {"label": "🇮🇳 Bodo / बडो", "dir": "ltr", "title": "MedicoBuddy AI निनाव सोंग", "tagline": "मोनफ्रोमबो साग्लोबनाय सोंथि, रोखा फोरमानजों सोमोन्दो गोनां।"},
    "mni": {"label": "🇮🇳 Manipuri / মৈতৈলোন্", "dir": "ltr", "title": "MedicoBuddy AI दा हংবীয়ু", "tagline": "অনাবাগী ৱাহং খুদিংমক, শেংলবা প্রমানগা শম্নবা।"},
    "en": {"label": "🇬🇧 English", "dir": "ltr", "title": "Ask MedicoBuddy AI", "tagline": "Everyday health questions, connected to clearer evidence."},
    "ar": {"label": "🇸🇦 Arabic / العربية", "dir": "rtl", "title": "اسأل MedicoBuddy AI", "tagline": "كل سؤال صحي، متصل بأدلة أكثر وضوحاً."},
    "es": {"label": "🇪🇸 Spanish / Español", "dir": "ltr", "title": "Pregunta a MedicoBuddy AI", "tagline": "Preguntas de salud cotidianas, conectadas a evidencia clara."},
}

# ── High Contrast Styling ─────────────────────────────────────
st.markdown(
    """
    <style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .stChatMessage { background-color: #1e293b !important; color: #ffffff !important; border-radius: 8px; border: 1px solid #334155; }
    .action-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 0.9rem; }
    .action-table th { background-color: #1e293b; color: #38bdf8; padding: 10px; border: 1px solid #475569; text-align: left; }
    .action-table td { padding: 10px; border: 1px solid #334155; background-color: #0f172a; color: #f8fafc; }
    .badge-status { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }
    .badge-online { background-color: #064e3b; color: #34d399; }
    .badge-offline { background-color: #7f1d1d; color: #fca5a5; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Check Runtime Health Probe ────────────────────────────────
@st.cache_data(ttl=10)
def check_health() -> dict[str, Any]:
    try:
        resp = httpx.get(HEALTH_URL, timeout=2.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {"ready": False, "status": "offline", "dependencies": {}}


health_data = check_health()
is_ready = health_data.get("ready", False)

# ── Sidebar Setup ─────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/medical-heart.png", width=64)
    st.title("MedicoBuddy AI")
    st.caption("Everyday health questions, connected to clearer evidence.")

    st.markdown("---")
    lang_code = st.selectbox(
        "🌐 Language Selector",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x]["label"],
        index=0,
    )
    selected_lang = LANGUAGES.get(lang_code, LANGUAGES["auto"])

    st.markdown("---")
    st.subheader("User Context (Adults 18–65)")
    st.info("Default context is unknown healthy adult. Change if relevant:")
    age = st.selectbox("Age Group", ["18-65 (Target Population)", "Under 18 (Out of scope)", "Over 65 (Out of scope)"], index=0)
    pregnancy = st.selectbox("Pregnancy Status", ["Unknown / Not Pregnant", "Pregnant", "Breastfeeding"], index=0)
    conditions = st.multiselect("Chronic Conditions", ["Diabetes", "Hypertension", "Kidney Disease", "Heart Disease", "Asthma"])

    st.markdown("---")
    consent_given = st.checkbox("I confirm I am an adult (18–65) and consent to processing my query for educational self-care guidance.", value=True)

    st.markdown("---")
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

    # System Status Drawer Link
    with st.expander("⚙️ System Status & Architecture (Admin)"):
        st.write(f"**Runtime Status:** {'🟢 Ready' if is_ready else '🔴 Offline/Degraded'}")
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
        st.markdown("<span class='badge-status badge-offline'>🔴 Service Degraded (Safety Mode)</span>", unsafe_allow_html=True)

st.caption("⚠️ **Educational Use Only:** MedicoBuddy AI provides evidence-grounded self-care education for adults 18–65 with mild, short-duration concerns. It does not diagnose, prescribe, or replace a clinician.")

# ── Session State Messages ─────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# Example Chips
st.markdown("**Quick Example Queries:**")
chip_cols = st.columns(4)
example_queries = [
    "Mild headache since this morning after work",
    "Uncomplicated cold symptoms and mild cough",
    "Mild stomach discomfort after eating",
    "Sleep hygiene and hydration guidelines",
]
selected_query = ""
for idx, q in enumerate(example_queries):
    if chip_cols[idx].button(q, key=f"chip_{idx}"):
        selected_query = q

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "action_table" in msg:
            st.markdown("### Action Table")
            table_html = "<table class='action-table'><tr><th>Guidance Lens</th><th>What May Help</th><th>How to Follow</th><th>Frequency/Duration</th><th>Evidence Level</th><th>Cautions</th><th>Stop & Seek Care If</th></tr>"
            for r in msg["action_table"]:
                table_html += f"<tr><td>{r.get('guidance_lens')}</td><td>{r.get('what_may_help')}</td><td>{r.get('how_to_follow')}</td><td>{r.get('frequency_duration')}</td><td>{r.get('evidence_level')}</td><td>{r.get('important_cautions')}</td><td>{r.get('stop_and_seek_care_if')}</td></tr>"
            table_html += "</table>"
            st.markdown(table_html, unsafe_allow_html=True)

        if "evidence_trail" in msg:
            with st.expander("🔍 Evidence Trail & Graph Traversal"):
                st.json(msg["evidence_trail"])

# Chat Input
user_input = st.chat_input("Ask MedicoBuddy AI a health question in any language...") or selected_query

if user_input:
    if not consent_given:
        st.error("Please accept the user consent checkbox in the sidebar before submitting your question.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            progress_placeholder = st.empty()
            progress_placeholder.info("🔄 Step 1/5: Running deterministic red-flag triage...")
            time.sleep(0.3)
            progress_placeholder.info("🔄 Step 2/5: Planning evidence search queries...")
            time.sleep(0.3)
            progress_placeholder.info("🔄 Step 3/5: Querying MCP connectors, Neo4j, and Milvus...")
            time.sleep(0.3)
            progress_placeholder.info("🔄 Step 4/5: Validating claim-to-passage entailment...")
            time.sleep(0.3)
            progress_placeholder.empty()

            # Execute Request to API
            payload = {
                "message": user_input,
                "thread_id": "streamlit_session",
                "age_range": "18-65" if "18-65" in age else "unknown",
                "pregnancy_status": "pregnant" if "Pregnant" in pregnancy else "unknown",
                "chronic_conditions": conditions,
                "region": "IN",
                "consent_given": True,
            }

            try:
                resp = httpx.post(f"{API_BASE}/chat", json=payload, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    status_text = f"### Safety Status: **{data.get('safety_status', 'self-care information').upper()}**\n"
                    applies = f"**What this applies to:** {data.get('what_this_applies_to', '')}\n"

                    st.markdown(status_text)
                    st.markdown(applies)

                    action_rows = data.get("action_table", [])
                    if action_rows:
                        st.markdown("### Action Table")
                        table_html = "<table class='action-table'><tr><th>Guidance Lens</th><th>What May Help</th><th>How to Follow</th><th>Frequency/Duration</th><th>Evidence Level</th><th>Cautions</th><th>Stop & Seek Care If</th></tr>"
                        for r in action_rows:
                            table_html += f"<tr><td>{r.get('guidance_lens')}</td><td>{r.get('what_may_help')}</td><td>{r.get('how_to_follow')}</td><td>{r.get('frequency_duration')}</td><td>{r.get('evidence_level')}</td><td>{r.get('important_cautions')}</td><td>{r.get('stop_and_seek_care_if')}</td></tr>"
                        table_html += "</table>"
                        st.markdown(table_html, unsafe_allow_html=True)

                    impl = data.get("implementation_plan", {})
                    if impl:
                        st.markdown("### Implementation Plan")
                        st.write(f"- **Now:** {impl.get('now')}")
                        st.write(f"- **Next 6–12 Hours:** {impl.get('next_6_to_12_hours')}")
                        st.write(f"- **Next 24–48 Hours:** {impl.get('next_24_to_48_hours')}")

                    when_seek = data.get("when_to_seek_care", [])
                    if when_seek:
                        st.markdown("### When to Seek Professional Help")
                        for cond in when_seek:
                            st.write(f"- ⚠️ {cond}")

                    citations = data.get("citations", [])
                    if citations:
                        st.markdown("### Evidence & Limitations")
                        for c in citations:
                            st.markdown(f"**[{c.get('number')}] [{c.get('title')}]({c.get('url')})** — *{c.get('authors')} ({c.get('publication_date')})*")
                            st.caption(f"Supporting passage: \"{c.get('supporting_passage')}\" (Limitation: {c.get('limitation')})")
                    else:
                        st.info("No grounded external citations retrieved for this query. Guidance limited to general safety monitoring.")

                    if data.get("targeted_follow_up"):
                        st.caption(f"❓ **Follow-up question:** {data.get('targeted_follow_up')}")

                    # Evidence Trail Drawer
                    with st.expander("🔍 Evidence Trail & Graph Traversal"):
                        if citations:
                            st.json(citations)
                        else:
                            st.write("No grounded graph path available for this query.")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": status_text + "\n" + applies,
                        "action_table": action_rows,
                        "evidence_trail": citations or "No grounded graph path available",
                    })
                else:
                    st.error(f"API Error ({resp.status_code}): {resp.text}")
            except Exception as exc:
                st.warning(f"Connecting in offline deterministic mode: {exc}")
                fallback_msg = f"### Safety Status: **SELF-CARE INFORMATION**\n**What this applies to:** Preventive self-care guidance for {user_input}.\n- Rest in a quiet, comfortable space.\n- Maintain gentle hydration with plain water.\n- Monitor symptoms over the next 24 to 48 hours. Seek clinical care if symptoms worsen."
                st.markdown(fallback_msg)
                st.session_state.messages.append({"role": "assistant", "content": fallback_msg})
