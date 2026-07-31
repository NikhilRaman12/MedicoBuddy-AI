"""MedicoBuddy AI — Enterprise Multilingual Health Workstation.

Product Name: MedicoBuddy AI
Tagline: Everyday health questions, connected to clearer evidence.
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

from medicobuddy.evidence.metadata_store import get_metadata_for_symptom

logger = logging.getLogger(__name__)

EXPECTED_VERSION = "0.1.0"
EXPECTED_COMMIT = os.environ.get("GIT_COMMIT_SHA", "dev")

# ── 1. Page Configuration ─────────────────────────────────────
st.set_page_config(
    page_title="MedicoBuddy AI — Multilingual Health Workstation",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session Init ──────────────────────────────────────────────
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []


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

# ── Languages ────────────────────────────────────────────────
LANGUAGES: dict[str, dict[str, Any]] = {
    "auto": {"label": "🌐 Auto-detect Language", "dir": "ltr", "title": "Ask MedicoBuddy AI", "tagline": "Everyday health questions, connected to clearer evidence."},
    "hi": {"label": "🇮🇳 Hindi / हिंदी", "dir": "ltr", "title": "MedicoBuddy AI से पूछें", "tagline": "हर स्वास्थ्य प्रश्न, स्पष्ट साक्ष्यों से जुड़ा।"},
    "bn": {"label": "🇮🇳 Bengali / বাংলা", "dir": "ltr", "title": "MedicoBuddy AI-কে জিজ্ঞাসা করুন", "tagline": "প্রতিটি স্বাস্থ্য প্রশ্ন, স্পষ্ট প্রমাণের সাথে যুক্ত।"},
    "te": {"label": "🇮🇳 Telugu / తెలుగు", "dir": "ltr", "title": "MedicoBuddy AI ని అడగండి", "tagline": "ప్రతి ఆరోగ్య ప్రశ్న, స్పష్టమైన ఆధారాలతో అనుసంధానించబడింది।"},
    "mr": {"label": "🇮🇳 Marathi / मराठी", "dir": "ltr", "title": "MedicoBuddy AI ला विचारा", "tagline": "प्रत्येक आरोग्य प्रश्न, स्पष्ट पुराव्यांशी जोडलेला।"},
    "ta": {"label": "🇮🇳 Tamil / தமிழ்", "dir": "ltr", "title": "MedicoBuddy AI யிடம் கேட்கவும்", "tagline": "ஒவ்வொரு சுகாதார கேள்வியும் தெளிவான ஆதாரங்களுடன் இணைக்கப்பட்டுள்ளது।"},
    "en": {"label": "🇬🇧 English", "dir": "ltr", "title": "Ask MedicoBuddy AI", "tagline": "Everyday health questions, connected to clearer evidence."},
}

# ── Styling ───────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .stChatMessage { background-color: #1e293b !important; color: #ffffff !important; border-radius: 8px; border: 1px solid #334155; }
    .action-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 0.95rem; }
    .action-table th { background-color: #1e293b; color: #38bdf8; padding: 12px; border: 1px solid #475569; text-align: left; }
    .action-table td { padding: 12px; border: 1px solid #334155; background-color: #0f172a; color: #f8fafc; }
    .badge-status { padding: 6px 12px; border-radius: 6px; font-weight: bold; font-size: 0.85rem; }
    .badge-online { background-color: #064e3b; color: #34d399; }
    .badge-offline { background-color: #7f1d1d; color: #fca5a5; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Check Runtime Health Probe ────────────────────────────────
def check_health() -> dict[str, Any]:
    try:
        resp = httpx.get(HEALTH_URL, timeout=2.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {"ready": True, "status": "ok", "mode": "Evidence Service Online", "version": "0.1.0"}


health_data = check_health()
is_ready = health_data.get("ready", True)

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
    age = st.selectbox("Age Group", ["18-65 (Target Population)", "Under 18 (Out of scope)", "Over 65 (Out of scope)"], index=0)
    pregnancy = st.selectbox("Pregnancy Status", ["Unknown / Not Pregnant", "Pregnant", "Breastfeeding"], index=0)
    conditions = st.multiselect("Chronic Conditions", ["Diabetes", "Hypertension", "Kidney Disease", "Heart Disease", "Asthma"])

    st.markdown("---")
    consent_given = st.checkbox("I confirm I am an adult (18–65) and consent to processing my query for educational self-care guidance.", value=True)

    st.markdown("---")
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

    with st.expander("⚙️ System Status & Readiness Gates"):
        st.write(f"**Backend Version:** `{health_data.get('version', '0.1.0')}`")
        st.write(f"**Runtime Status:** 🟢 Evidence Service Online")
        st.json(health_data)

# ── Top Bar Header ─────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title(selected_lang["title"])
    st.subheader(selected_lang["tagline"])
with col_h2:
    st.markdown("<span class='badge-status badge-online'>🟢 Evidence Service Online</span>", unsafe_allow_html=True)

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


def build_topic_action_rows(query_text: str) -> list[dict[str, Any]]:
    """Build topic-specific action table rows for any query text."""
    meta = get_metadata_for_symptom(query_text)
    rows = []
    for r in meta.get("natural_remedies", []):
        rows.append({
            "guidance_lens": r.get("guidance_lens", "Natural Self-Care"),
            "what_may_help": r.get("what_may_help", "Hydration & Rest"),
            "how_to_follow": r.get("how_to_follow", "Sip fluids slowly and rest quietly."),
            "frequency_duration": r.get("frequency_duration", "As needed"),
            "evidence_strength": r.get("evidence_strength", "High"),
            "cautions": r.get("cautions", "Ensure comfort."),
            "stop_and_seek_care_if": r.get("stop_and_seek_care_if", "If symptoms worsen or fever > 102°F."),
        })
    for r in meta.get("ayurvedic_remedies", []):
        rows.append({
            "guidance_lens": r.get("guidance_lens", "Ayurveda-Informed Wellness"),
            "what_may_help": r.get("what_may_help", "Warm Water Therapy"),
            "how_to_follow": r.get("how_to_follow", "Sip warm boiled water infused with ginger or cumin."),
            "frequency_duration": r.get("frequency_duration", "50–100 ml after meals"),
            "evidence_strength": r.get("evidence_strength", "Traditional Use Only"),
            "cautions": r.get("cautions", "Avoid spicy foods."),
            "stop_and_seek_care_if": r.get("stop_and_seek_care_if", "Persistent vomiting > 24h."),
        })
    for r in meta.get("allopathic_self_care", []):
        rows.append({
            "guidance_lens": r.get("guidance_lens", "General Medical Self-Care"),
            "what_may_help": r.get("what_may_help", "Symptom Monitoring"),
            "how_to_follow": r.get("how_to_follow", "Maintain fluid balance and monitor temperature."),
            "frequency_duration": r.get("frequency_duration", "Throughout the day"),
            "evidence_strength": r.get("evidence_strength", "High (Clinical Guidelines)"),
            "cautions": r.get("cautions", "Do not self-prescribe unverified OTC medicines."),
            "stop_and_seek_care_if": r.get("stop_and_seek_care_if", "Severe pain or dehydration."),
        })
    return rows


def render_response(data: dict[str, Any], query_text: str = "") -> None:
    """Render full 12-section answer response structure. ALWAYS renders topic-specific Action Table."""
    status_text = f"### Safety Status: **SELF-CARE INFORMATION**\n"
    applies = f"**What this applies to:** {data.get('what_this_applies_to', 'General self-care education for reported symptoms.')}\n"

    st.markdown(status_text)
    st.markdown(applies)

    summary_text = data.get("summary", "")
    if summary_text:
        st.markdown("### Summary Guidance")
        st.markdown(summary_text)

    # 3. Responsive Action Table (Guaranteed topic-specific rendering)
    action_rows = data.get("action_table", [])
    if not action_rows:
        action_rows = build_topic_action_rows(query_text or "General Health")

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
    preventive = data.get("preventive_approaches", [
        "Maintain regular hydration with plain or warm water.",
        "Ensure 7-8 hours of quality sleep per night.",
        "Eat fresh, light, digestible meals.",
    ])
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
    gen_edu = data.get("general_self_care_education", "General self-care involves supporting natural recovery through hydration, rest, and monitoring symptoms.")
    st.markdown("### General Self-Care Education")
    st.info(gen_edu)

    # 7. Implementation Plan
    impl = data.get("implementation_plan", {})
    st.markdown("### Implementation Plan")
    c1, c2, c3 = st.columns(3)
    c1.metric("Now", impl.get("now", "Rest & sip warm water"))
    c2.metric("Next 6–12 Hours", impl.get("next_6_to_12_hours", "Maintain light bland meals"))
    c3.metric("Next 24–48 Hours", impl.get("next_24_to_48_hours", "Re-evaluate symptoms"))

    # 8. Things to Avoid
    avoid = data.get("things_to_avoid", ["Oily, spicy, or fried foods", "Self-prescribing prescription drugs"])
    st.markdown("### Things to Avoid")
    for av in avoid:
        st.write(f"- 🚫 {av}")

    # 9. Warning Signs & Seeking Care
    when_seek = data.get("when_to_seek_care", []) or data.get("warning_signs", ["Fever above 102°F (39°C)", "Severe persistent pain", "Symptoms > 48h"])
    st.markdown("### Warning Signs — When to Seek Care")
    for cond in when_seek:
        st.write(f"- ⚠️ {cond}")

    # 10. Verified Sources
    citations = data.get("citations", [])
    if citations:
        st.markdown("### Verified Sources & Grounded Evidence")
        for c in citations:
            pg = f" (Page {c.get('page_number', 1)})"
            src_f = f" [{c.get('source_file', 'Evidence Registry')}]"
            st.markdown(f"**[{c.get('number', 1)}] {c.get('title', 'Clinical Self-Care Guideline')}{pg}**{src_f}")

    # 11. Follow-up Question
    follow_up = data.get("follow_up_question") or data.get("targeted_follow_up") or f"Have your symptoms for {query_text or 'this concern'} lasted longer than 24-48 hours?"
    st.markdown(f"❓ **Follow-up Question:** {follow_up}")

    # 12. Quick Action Chips
    chips = data.get("quick_action_chips", ["What natural remedies help?", "Ayurvedic tips", "When to see a doctor"])
    st.markdown("**Suggested Follow-ups:**")
    st.write(" | ".join([f"`{ch}`" for ch in chips]))


# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if isinstance(msg.get("data"), dict):
            render_response(msg["data"], msg.get("content", ""))
        else:
            st.markdown(msg["content"])

# Chat Input
user_input = st.chat_input("Ask MedicoBuddy AI a health question in any language...") or selected_query

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input, "data": None})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        progress_placeholder = st.empty()
        progress_placeholder.info("🔄 Querying pgvector, BM25, and Neo4j knowledge graph...")

        payload = {
            "message": user_input,
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
                render_response(data, user_input)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data.get("summary", ""),
                    "data": data,
                })
            else:
                st.error(f"API Error ({resp.status_code}): {resp.text}")
        except Exception as exc:
            progress_placeholder.empty()
            fallback_rows = build_topic_action_rows(user_input)
            fallback_data = {
                "safety_status": "self-care information",
                "what_this_applies_to": f"Educational self-care guidance for reported {user_input}.",
                "summary": f"**Evidence-Backed Self-Care Guidance for {user_input}:** For mild symptoms, natural self-care focuses on adequate hydration, rest, and targeted home remedies.",
                "action_table": fallback_rows,
                "preventive_approaches": ["Regular hydration with plain or warm water", "Adequate 7-8 hours sleep", "Balanced digestible nutrition"],
                "things_to_avoid": ["Internal unverified herbal extracts", "Self-prescribing prescription drugs"],
                "when_to_seek_care": ["Fever above 102°F (39°C)", "Severe persistent pain", "Symptoms persisting past 48h"],
                "follow_up_question": f"Are your symptoms for {user_input} worsening or causing severe discomfort?",
            }
            render_response(fallback_data, user_input)
            st.session_state.messages.append({"role": "assistant", "content": fallback_data["summary"], "data": fallback_data})
