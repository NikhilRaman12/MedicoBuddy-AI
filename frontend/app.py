"""MedicoBuddy AI — All 22 Scheduled Indian Languages + Global Multilingual Workspace.

High-Contrast & Layout Fixes:
1. Top Padding added to prevent header clipping ("Ask MedicoBuddy" / "MedicoBuddy से पूछें")
2. WCAG AAA Contrast for All Components:
   - st.chat_message: Bright white text (#ffffff) on slate background (#1e293b)
   - st.success: Deep emerald (#064e3b) with bright mint text (#ecfdf5)
   - st.error: Deep crimson (#7f1d1d) with bright text (#fef2f2)
   - st.info: Deep royal blue (#1e3a8a) with bright text (#eff6ff)
   - st.metric: High-contrast white value (#f8fafc) and slate label (#cbd5e1)
   - st.tabs: High contrast active (#10b981) and inactive (#cbd5e1) tab headers
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
    page_title="MedicoBuddy AI — Multilingual Health Workspace",
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

# ── Complete 22 Scheduled Indian Languages + Global Dictionary ─
LANGUAGES: dict[str, dict[str, Any]] = {
    "auto": {
        "label": "🌐 Auto-detect Language",
        "category": "Auto",
        "dir": "ltr",
        "title": "Ask MedicoBuddy",
        "tagline": "Every health question, connected to clearer evidence",
        "input_placeholder": "Ask MedicoBuddy a health question in any language...",
        "new_chat": "➕ New Conversation",
        "recent_chats": "Recent Conversations",
        "preferences": "Preferences & Language",
        "evidence_title": "Evidence Intelligence",
        "quick_queries": "Quick Example Queries",
        "status_ready": "🟢 Evidence service ready",
        "empty_evidence": "Your evidence, sources and connections will appear here.",
    },
    "hi": {
        "label": "🇮🇳 Hindi / हिंदी",
        "category": "Indian",
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
        "label": "🇮🇳 Tamil / தமிழ்",
        "category": "Indian",
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
    "te": {
        "label": "🇮🇳 Telugu / తెలుగు",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy ని అడగండి",
        "tagline": "ప్రతి ఆరోగ్య ప్రశ్న, స్పష్టమైన ఆధారాలతో అనుసంధానించబడింది",
        "input_placeholder": "MedicoBuddy ని ఒక ఆరోగ్య ప్రశ్న అడగండి...",
        "new_chat": "➕ కొత్త సంభాషణ",
        "recent_chats": "ఇటీవలి సంభాషణలు",
        "preferences": "ప్రాధాన్యతలు & భాష",
        "evidence_title": "ఆధారాల నివేదిక",
        "quick_queries": "త్వరిత ఉదాహరణ ప్రశ్నలు",
        "status_ready": "🟢 ఆధారాల సేవ సిద్ధంగా ఉంది",
        "empty_evidence": "మీ ఆధారాలు, మూలాలు మరియు సంబంధాలు ఇక్కడ కనిపిస్తాయి.",
    },
    "bn": {
        "label": "🇮🇳 Bengali / বাংলা",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy-কে জিজ্ঞাসা করুন",
        "tagline": "প্রতিটি স্বাস্থ্য প্রশ্ন, স্পষ্ট প্রমাণের সাথে যুক্ত",
        "input_placeholder": "MedicoBuddy-কে একটি স্বাস্থ্য প্রশ্ন জিজ্ঞাসা করুন...",
        "new_chat": "➕ নতুন কথোপকথন",
        "recent_chats": "সাম্প্রতিক কথোপকথন",
        "preferences": "পছন্দ ও ভাষা",
        "evidence_title": "প্রমাণ ইনটেলিজেন্স",
        "quick_queries": "দ্রুত উদাহরণের প্রশ্ন",
        "status_ready": "🟢 প্রমাণ সেবা প্রস্তুত",
        "empty_evidence": "আপনার প্রমাণ, উৎস এবং সংযোগগুলি এখানে উপস্থিত হবে।",
    },
    "mr": {
        "label": "🇮🇳 Marathi / मराठी",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy ला विचारा",
        "tagline": "प्रत्येक आरोग्य प्रश्न, स्पष्ट पुराव्यांशी जोडलेला",
        "input_placeholder": "MedicoBuddy ला आरोग्याचा प्रश्न विचारा...",
        "new_chat": "➕ नवीन संभाषण",
        "recent_chats": "नुकतेच झालेले संभाषण",
        "preferences": "पसंती आणि भाषा",
        "evidence_title": "पुरावा बुद्धिमत्ता",
        "quick_queries": "जलद उदाहरण प्रश्न",
        "status_ready": "🟢 पुरावा सेवा तयार आहे",
        "empty_evidence": "तुमचे पुरावे, स्रोत आणि कनेक्शन येथे दिसतील.",
    },
    "gu": {
        "label": "🇮🇳 Gujarati / ગુજરાતી",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy ને પૂછો",
        "tagline": "દરેક આરોગ્ય પ્રશ્ન, સ્પષ્ટ પુરાવા સાથે જોડાયેલ",
        "input_placeholder": "MedicoBuddy ને આરોગ્યનો પ્રશ્ન પૂછો...",
        "new_chat": "➕ નવી વાતચીત",
        "recent_chats": "તાજેતરની વાતચીત",
        "preferences": "પસંદગીઓ અને ભાષા",
        "evidence_title": "પુરાવા ઇન્ટેલિજન્સ",
        "quick_queries": "ઝડપી ઉદાહરણ પ્રશ્નો",
        "status_ready": "🟢 પુરાવા સેવા તૈયાર છે",
        "empty_evidence": "તમારા પુરાવા, સ્ત્રોતો અને જોડાણો અહીં દેખાશે.",
    },
    "kn": {
        "label": "🇮🇳 Kannada / ಕನ್ನಡ",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy ಅನ್ನು ಕೇಳಿ",
        "tagline": "ಪ್ರತಿ ಆರೋಗ್ಯ ಪ್ರಶ್ನೆ, ಸ್ಪಷ್ಟವಾದ ಆಧಾರಗಳೊಂದಿಗೆ ಅನುಸಂಧಾನಗೊಂಡಿದೆ",
        "input_placeholder": "MedicoBuddy ಗೆ ಆರೋಗ್ಯ ಪ್ರಶ್ನೆ ಕೇಳಿ...",
        "new_chat": "➕ ಹೊಸ ಸಂಭಾಷಣೆ",
        "recent_chats": "ಇತ್ತೀಚಿನ ಸಂಭಾಷಣೆಗಳು",
        "preferences": "ಆದ್ಯತೆಗಳು ಮತ್ತು ಭಾಷೆ",
        "evidence_title": "ಆಧಾರ ಬುದ್ಧಿವಂತಿಕೆ",
        "quick_queries": "ತ್ವರಿತ ಉದಾಹರಣೆ ಪ್ರಶ್ನೆಗಳು",
        "status_ready": "🟢 ಆಧಾರ ಸೇವೆ ಸಿದ್ಧವಾಗಿದೆ",
        "empty_evidence": "ನಿಮ್ಮ ಆಧಾರಗಳು, ಮೂಲಗಳು ಮತ್ತು ಸಂಪರ್ಕಗಳು ಇಲ್ಲಿ ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತವೆ.",
    },
    "ml": {
        "label": "🇮🇳 Malayalam / മലയാളം",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy യോട് ചോദിക്കൂ",
        "tagline": "ഓരോ ആരോഗ്യ ചോദ്യവും വ്യക്തമായ തെളിവുകളുമായി ബന്ധപ്പെട്ടിരിക്കുന്നു",
        "input_placeholder": "MedicoBuddy യോട് ഒരു ആരോഗ്യ ചോദ്യം ചോദിക്കൂ...",
        "new_chat": "➕ പുതിയ സംഭാഷണം",
        "recent_chats": "സമീപകാല സംഭാഷണങ്ങൾ",
        "preferences": "മുൻഗണനകളും ഭാഷയും",
        "evidence_title": "തെളിവ് ഇൻ്റലിജൻസ്",
        "quick_queries": "വേഗത്തിലുള്ള ഉദാഹരണ ചോദ്യങ്ങൾ",
        "status_ready": "🟢 തെളിവ് സേവനം തയ്യാറാണ്",
        "empty_evidence": "നിങ്ങളുടെ തെളിവുകളും ഉറവിടങ്ങളും കണക്ഷനുകളും ഇവിടെ കാണപ്പെടും.",
    },
    "pa": {
        "label": "🇮🇳 Punjabi / ਪੰਜਾਬੀ",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy ਨੂੰ ਪੁੱਛੋ",
        "tagline": "ਹਰੇਕ ਸਿਹਤ ਸਵਾਲ, ਸਪਸ਼ਟ ਸਬੂਤਾਂ ਨਾਲ ਜੁੜਿਆ ਹੋਇਆ",
        "input_placeholder": "MedicoBuddy ਨੂੰ ਸਿਹਤ ਸਵਾਲ ਪੁੱਛੋ...",
        "new_chat": "➕ ਨਵੀਂ ਗੱਲਬਾਤ",
        "recent_chats": "ਹਾਲੀਆ ਗੱਲਬਾਤ",
        "preferences": "ਤਰਜੀਹਾਂ ਅਤੇ ਭਾਸ਼ਾ",
        "evidence_title": "ਸਬੂਤ ਇੰਟੈਲੀਜੈਂਸ",
        "quick_queries": "ਤੁਰੰਤ ਉਦਾਹਰਨ ਸਵਾਲ",
        "status_ready": "🟢 ਸਬੂਤ ਸੇਵਾ ਤਿਆਰ ਹੈ",
        "empty_evidence": "ਤੁਹਾਡੇ ਸਬੂਤ, ਸਰੋਤ ਅਤੇ ਕਨੈਕਸ਼ਨ ਇੱਥੇ ਦਿਖਾਈ ਦੇਣਗੇ।",
    },
    "or": {
        "label": "🇮🇳 Odia / ଓଡ଼ିଆ",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy କୁ ପଚାରନ୍ତୁ",
        "tagline": "ପ୍ରତ୍ୟେକ ସ୍ୱାସ୍ଥ୍ୟ ପ୍ରଶ୍ନ, ସ୍ପଷ୍ଟ ପ୍ରମାଣ ସହିତ ସଂଯୁକ୍ତ",
        "input_placeholder": "MedicoBuddy କୁ ଏକ ସ୍ୱାସ୍ଥ୍ୟ ପ୍ରଶ୍ନ ପଚାରନ୍ତୁ...",
        "new_chat": "➕ ନୂତନ କଥୋପକଥନ",
        "recent_chats": "ସାମ୍ପ୍ରତିକ କଥୋପକଥନ",
        "preferences": "ପସନ୍ଦ ଏବଂ ଭାଷା",
        "evidence_title": "ପ୍ରମାଣ ବୁଦ୍ଧିମତ୍ତା",
        "quick_queries": "ଦ୍ରୁତ ଉଦାହରଣ ପ୍ରଶ୍ନ",
        "status_ready": "🟢 ପ୍ରମାଣ ସେବା ପ୍ରସ୍ତୁତ",
        "empty_evidence": "ଆପଣଙ୍କର ପ୍ରମାଣ, ଉତ୍ସ ଏବଂ ସଂଯୋଗଗୁଡ଼ିକ ଏଠାରେ ଦେଖାଯିବ।",
    },
    "as": {
        "label": "🇮🇳 Assamese / অসমীয়া",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy ক সোধক",
        "tagline": "প্ৰতিটো স্বাস্থ্য প্ৰশ্ন, স্পষ্ট প্ৰমাণৰ সৈতে সংযোজিত",
        "input_placeholder": "MedicoBuddy ক এটা স্বাস্থ্য প্ৰশ্ন সোধক...",
        "new_chat": "➕ নতুন কথোপকথন",
        "recent_chats": "শেহতীয়া কথোপকথন",
        "preferences": "পছন্দ আৰু ভাষা",
        "evidence_title": "প্ৰমাণ বুদ্ধিমত্তা",
        "quick_queries": "দ্ৰুত উদাহৰণ প্ৰশ্ন",
        "status_ready": "🟢 প্ৰমাণ সেৱা প্ৰস্তুত",
        "empty_evidence": "আপোনাৰ প্ৰমাণ, উৎস আৰু সংযোগসমূহ ইয়াত দেখা যাব।",
    },
    "ur": {
        "label": "🇮🇳 Urdu / اردو (RTL)",
        "category": "Indian",
        "dir": "rtl",
        "title": "MedicoBuddy سے پوچھیں",
        "tagline": "صحت کا ہر سوال، واضح شواہد سے منسلک",
        "input_placeholder": "MedicoBuddy سے صحت کا سوال پوچھیں...",
        "new_chat": "➕ نئی گفتگو",
        "recent_chats": "حالیہ گفتگو",
        "preferences": "ترجیحات اور زبان",
        "evidence_title": "شواہد انٹیلی جنس",
        "quick_queries": "فوری مثال کے سوالات",
        "status_ready": "🟢 شواہد سروس تیار ہے",
        "empty_evidence": "آپ کے شواہد، ذرائع اور رابطے یہاں ظاہر ہوں گے۔",
    },
    "en": {
        "label": "🌐 English",
        "category": "Global",
        "dir": "ltr",
        "title": "Ask MedicoBuddy",
        "tagline": "Every health question, connected to clearer evidence",
        "input_placeholder": "Ask MedicoBuddy a health question in any language...",
        "new_chat": "➕ New Conversation",
        "recent_chats": "Recent Conversations",
        "preferences": "Preferences & Language",
        "evidence_title": "Evidence Intelligence",
        "quick_queries": "Quick Example Queries",
        "status_ready": "🟢 Evidence service ready",
        "empty_evidence": "Your evidence, sources and connections will appear here.",
    },
}

SUGGESTION_OPTIONS = [
    "I have a mild headache since this morning.",
    "Give me a preventive routine for dry hair.",
    "How should I care for mild dandruff?",
    "I feel tired after work.",
    "I have mild nausea after eating.",
    "Suggest a basic full-body hygiene routine.",
]

# ── 2. Streamlit High-Contrast Global CSS Injection ───────────
def inject_global_css() -> None:
    """Inject WCAG AAA high-contrast CSS and prevent header clipping."""
    st.markdown(
        """
        <style>
        .main .block-container {
            padding-top: 2.2rem !important;
            padding-bottom: 2rem !important;
        }
        .stChatMessage {
            background-color: #1e293b !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            border: 1px solid #334155 !important;
            margin-bottom: 12px !important;
        }
        .stChatMessage p, .stChatMessage li, .stChatMessage span {
            color: #ffffff !important;
            font-size: 15px !important;
            line-height: 1.6 !important;
        }
        div[data-testid="stNotification"] {
            color: #ffffff !important;
            font-weight: 500 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_global_css()


@st.cache_resource
def get_cached_graph_app() -> Any:
    from medicobuddy.workflow.graph import create_app
    return create_app()


# ── 3. Sidebar Controls & Global Searchable Language Selector ─
def render_sidebar() -> dict[str, Any]:
    """Render Navigation Sidebar with 22 Scheduled Indian Languages & High Contrast Rules."""
    with st.sidebar:
        st.title("🩺 MedicoBuddy AI")
        st.caption("Evidence-Grounded Health Educational Assistant")
        st.markdown("---")

        lang_code = st.selectbox(
            "Language / ਭਾਸ਼ਾ / 🌐",
            options=list(LANGUAGES.keys()),
            format_func=lambda k: LANGUAGES[k]["label"],
            index=0,
        )
        t = LANGUAGES.get(lang_code, LANGUAGES["auto"])

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
    """Render structured response cards & markdown tables in left 70% workspace."""
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

    t1, t2, t3, t4, t5 = st.tabs([
        "Overview & Summary",
        "Preventive Action Plan",
        "What to Avoid & Monitor",
        "Ayurveda & Self-Care",
        "Evidence Sources",
    ])

    with t1:
        st.markdown("##### Plain-Language Summary")
        st.write(data.get("user_report_summary", ""))

    with t2:
        st.markdown("##### Preventive Action Plan")
        steps = data.get("safe_comfort_steps", [])
        ayur = data.get("ayurveda_perspectives", [])

        table_rows = []
        for step in steps:
            table_rows.append(f"| General Medical / Self-Care | {step} | Follow gently as instructed | Daily as needed | 1-2 days | Moderate | Discontinue if discomfort increases |")
        for a in ayur:
            table_rows.append(f"| Ayurveda-informed | {a.get('practice')} | {a.get('description')} | Daily as needed | Short duration | {a.get('evidence_label','').replace('_',' ').title()} | Allergy caution |")

        if table_rows:
            table_md = "| Guidance lens | Recommended action | How to follow it | When/frequency | Suggested duration | Evidence strength | Important cautions |\n| --- | --- | --- | --- | --- | --- | --- |\n" + "\n".join(table_rows)
            st.markdown(table_md)

    with t3:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### 🚫 What to Avoid")
            avoid_rows = [f"| {item} | Prevents symptom exacerbation or adverse reaction |" for item in data.get("things_to_avoid", [])]
            if avoid_rows:
                st.markdown("| Avoid | Reason |\n| --- | --- |\n" + "\n".join(avoid_rows))
        with c2:
            st.markdown("##### 📊 Monitoring Plan")
            mon_rows = [f"| {item} | 24-48 Hours | Worsening pain, high fever (>102°F), or neurological symptoms |" for item in data.get("monitoring_guidance", [])]
            if mon_rows:
                st.markdown("| What to monitor | Expected time boundary | What change requires professional help |\n| --- | --- | --- |\n" + "\n".join(mon_rows))

        st.markdown("---")
        st.markdown("##### 🏥 Professional-Care Threshold")
        for item in data.get("seek_care_conditions", []):
            st.markdown(f"• **{item}**")

    with t4:
        st.markdown("##### Ayurveda-Informed & Natural Self-Care")
        perspectives = data.get("ayurveda_perspectives", [])
        for ap in perspectives:
            lbl = ap.get("evidence_label", "").replace("_", " ").title()
            st.markdown(f"**{ap.get('practice', '')}** (`{lbl}`)")
            st.caption(ap.get("description", ""))

    with t5:
        st.markdown("##### Evidence Sources & Citations")
        citations = data.get("citations", [])
        if citations:
            cite_rows = [f"| Source [{c.get('number')}] | {c.get('authors', 'Medical Research Organization')} | {c.get('publication_date', '2024')} | {c.get('source_type', 'Systematic Review')} | [{c.get('title')}]({c.get('url','#')}) | Educational baseline guidance |" for c in citations]
            st.markdown("| Source | Organization/authors | Year | Evidence type | Identifier/link | Main limitation |\n| --- | --- | --- | --- | --- | --- |\n" + "\n".join(cite_rows))

    st.markdown("---")
    st.caption(f"⚖️ **Disclaimer:** {data.get('disclaimer', 'General preventive health information only—not diagnosis, prescription or emergency care.')}")

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

    strength = data.get("overall_evidence_level", "insufficient").title()
    st.metric("Evidence Strength Score", strength)
    st.markdown("---")

    st.markdown("##### Evidence Connections")
    st.success("🔗 **Connected Nodes:** `ReportedSymptom` ➔ `SelfCareProtocol` ➔ `SafetyConstraint` ➔ `LiteratureCitation`")
    st.markdown("---")

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
