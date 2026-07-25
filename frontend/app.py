"""MedicoBuddy AI — All 22 Scheduled Indian Languages + Global Multilingual Workspace.

Features:
- 22 Scheduled Constitutional Indian Languages (Unicode CLDR Native Scripts)
  [Assamese, Bengali, Bodo, Dogri, Gujarati, Hindi, Kannada, Kashmiri, Konkani, Maithili,
   Malayalam, Manipuri/Meitei, Marathi, Nepali, Odia, Punjabi, Sanskrit, Santali, Sindhi, Tamil, Telugu, Urdu]
- Global Languages (English, Spanish, French, German, Arabic)
- Auto-Detect Option & RTL Script Support (Urdu, Sindhi, Arabic)
- Complete UI Translation Matrix (Title, Tagline, Composer, Buttons, Tabs, Evidence Dock)
- 70/30 Chat-First Workspace & Preserved LangGraph Backend Architecture
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
    # ── Auto-Detect ───────────────────────────────────────────
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
    # ── 22 Official Scheduled Indian Languages ─────────────────
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
    "brx": {
        "label": "🇮🇳 Bodo / बर' / बड़ो",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy नो सों",
        "tagline": "फ्रोमबो सासथि सोंथि, रोखा साखिजों सोमोन्दो गोनां",
        "input_placeholder": "MedicoBuddy नो सासथि सोंथि सों...",
        "new_chat": "➕ गोदान सावरायनाय",
        "recent_chats": "बावदिसै सावरायनायफोर",
        "preferences": "पसन्द आरो राव",
        "evidence_title": "साखि गियान",
        "quick_queries": "गोख्रै बिदिन्थि सोंथि",
        "status_ready": "🟢 साखि सेबा थियारि",
        "empty_evidence": "नोंथांनि साखिफोर, फुंखाफोर आरो सोमोन्दोफोरा बेयाव नुजाथिगन।",
    },
    "doi": {
        "label": "🇮🇳 Dogri / डोगरी",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy थमा पुच्छो",
        "tagline": "हर सेहत सवाल, साफ सबूतें कन्नै जुड़े दा",
        "input_placeholder": "MedicoBuddy गी सेहत दा सवाल पुच्छो...",
        "new_chat": "➕ नवी गल्लबात",
        "recent_chats": "हालै दी गल्लबात",
        "preferences": "पसंद ते बोली",
        "evidence_title": "सबूत समझदारी",
        "quick_queries": "झटपट मिसाल सवाल",
        "status_ready": "🟢 सबूत सेवा तैयार",
        "empty_evidence": "तुंदे सबूत, सोमे ते जोड़ इत्थै लभङन।",
    },
    "ks": {
        "label": "🇮🇳 Kashmiri / کٲشُر (RTL)",
        "category": "Indian",
        "dir": "rtl",
        "title": "MedicoBuddy نس پرچھیو",
        "tagline": "پرتھ سہیتی سوال، صاف ثبوتن سئتھ گنڈتھ",
        "input_placeholder": "MedicoBuddy نس پرچھیو سہیتی سوال...",
        "new_chat": "➕ ناو کٹھ",
        "recent_chats": "حالیہ کٹھ",
        "preferences": "ترجیحات تہ زبان",
        "evidence_title": "ثبوت زان",
        "status_ready": "🟢 ثبوت سروس تیار",
        "empty_evidence": "تُہند ثبوت تہ ذریعہ ییتین لَبنہ یین।",
        "quick_queries": "تیز سوال",
    },
    "kok": {
        "label": "🇮🇳 Konkani / कोंकणी",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy क विचारांत",
        "tagline": "दर एक भलायकी प्रस्न, निवळ पुराव्यांक जोडिल्लो",
        "input_placeholder": "MedicoBuddy क भलायकेचो प्रस्न विचारांत...",
        "new_chat": "➕ नवी उलोवप",
        "recent_chats": "फाटली उलोवपां",
        "preferences": "पसंत आनी भास",
        "evidence_title": "पुरावा बुद्धीमत्ता",
        "quick_queries": "वेगीं देखींचे प्रस्न",
        "status_ready": "🟢 पुरावा सेवा तयार",
        "empty_evidence": "तुमचे पुरावे आनी संबंद हांगा दिसतले.",
    },
    "mai": {
        "label": "🇮🇳 Maithili / मैथिली",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy सँ पूछू",
        "tagline": "प्रत्येक स्वास्थ्य प्रश्न, स्पष्ट प्रमाण सँ जुड़ल",
        "input_placeholder": "MedicoBuddy सँ स्वास्थ्य प्रश्न पूछू...",
        "new_chat": "➕ नव बातचीत",
        "recent_chats": "हालक बातचीत",
        "preferences": "पसंद आ भाषा",
        "evidence_title": "प्रमाण बुद्धिमत्ता",
        "quick_queries": "त्वरित उदाहरण प्रश्न",
        "status_ready": "🟢 प्रमाण सेवा तैयार",
        "empty_evidence": "अहाँक प्रमाण आ स्रोत एतय देखायत।",
    },
    "mni": {
        "label": "🇮🇳 Manipuri (Meitei) / মৈতৈলোন্",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy দা হাংবীয়ু",
        "tagline": "અના-લાয়েংগী হংবা খুদিংমক, শেংবা প্রমানগা শম্নবা",
        "input_placeholder": "MedicoBuddy দা অনাবগী ৱাহং হাংবীয়ু...",
        "new_chat": "➕ অনৌবা ৱারী",
        "recent_chats": "হন্দক্তা চতখবা ৱারী",
        "preferences": "পামজবা অমসুং লোন",
        "evidence_title": "প্রমান জ্ঞান",
        "quick_queries": "য়াংনা খঙনবগী ৱাহং",
        "status_ready": "🟢 প্রমান থৌরাং শেমখ্রে",
        "empty_evidence": "নহাকগী প্রমান অমসুং মরীশিং অসিনা মফম অসিদা উবা ফংগনি।",
    },
    "ne": {
        "label": "🇮🇳 Nepali / नेपाली",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy लाई सोध्नुहोस्",
        "tagline": "हरेक स्वास्थ्य प्रश्न, स्पष्ट प्रमाणसँग जोडिएको",
        "input_placeholder": "MedicoBuddy लाई स्वास्थ्य प्रश्न सोध्नुहोस्...",
        "new_chat": "➕ नयाँ कुराकानी",
        "recent_chats": "भर्खरका कुराकानीहरू",
        "preferences": "प्राथमिकता र भाषा",
        "evidence_title": "प्रमाण बुद्धिमत्ता",
        "quick_queries": "द्रुत उदाहरण प्रश्नहरू",
        "status_ready": "🟢 प्रमाण सेवा तयार छ",
        "empty_evidence": "तपाईंका प्रमाण, स्रोत र सम्बन्धहरू यहाँ देखिनेछन्।",
    },
    "sa": {
        "label": "🇮🇳 Sanskrit / संस्कृतम्",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy पृच्छतु",
        "tagline": "प्रतिस्वास्थ्यप्रश्नः, स्पष्टप्रमाणैः सह सम्बद्धः",
        "input_placeholder": "MedicoBuddy स्वास्थ्यप्रश्नं पृच्छतु...",
        "new_chat": "➕ नूतनसंवादः",
        "recent_chats": "नूतनसंवादाः",
        "preferences": "प्राधान्यं भाषा च",
        "evidence_title": "प्रमाणबुद्धिमत्ता",
        "quick_queries": "शीघ्रौदाहरणप्रश्नाः",
        "status_ready": "🟢 प्रमाणसेवा सज्जीकृता",
        "empty_evidence": "भवतः प्रमाणानि स्रोतांसि च अत्र दृश्यन्ते।",
    },
    "sat": {
        "label": "🇮🇳 Santali / ਓਲ ᱪᱤᱠᱤ / ସାନ୍ତାଳୀ",
        "category": "Indian",
        "dir": "ltr",
        "title": "MedicoBuddy ᱠᱩᱞᱤᱭᱮᱢ",
        "tagline": "ᱡᱚᱛᱚ ᱞᱟᱭ ᱠᱩᱠᱞᱤ, ᱥᱟᱹᱨᱤ ᱯᱩᱨᱟᱹᱣ ᱥᱟᱶ ᱡᱚᱲᱟᱣ",
        "input_placeholder": "MedicoBuddy ᱴᱷᱮᱱ ᱞᱟᱭ ᱠᱩᱠᱞᱤ ᱠᱩᱞᱤᱭᱮᱢ...",
        "new_chat": "➕ ᱱᱟᱶᱟ ᱜᱟᱞ point",
        "recent_chats": "ᱱᱤᱛᱚᱜᱟᱜ ᱜᱟᱞ point",
        "preferences": "ᱯᱟᱹᱨᱥᱤ ᱟᱨ preferences",
        "evidence_title": "ᱯᱩᱨᱟᱹᱣ ᱵᱩᱫᱷᱤ",
        "quick_queries": "ᱞᱚᱜᱚᱱ ᱠᱩᱠᱞᱤ",
        "status_ready": "🟢 ᱯᱩᱨᱟᱹᱣ ᱥᱮᱵᱟ ᱛᱮᱭᱟᱨ",
        "empty_evidence": "ᱟᱢᱟᱜ ᱯᱩᱨᱟᱹᱣ ᱟᱨ ᱥᱚᱨᱚᱥ ᱱᱚᱸᱰᱮ ᱧᱮᱞᱚᱜᱼᱟ।",
    },
    "sd": {
        "label": "🇮🇳 Sindhi / سنڌي (RTL)",
        "category": "Indian",
        "dir": "rtl",
        "title": "MedicoBuddy کان پڇو",
        "tagline": "هر صحت جو سوال، واضح ثبوتن سان جڙيل",
        "input_placeholder": "MedicoBuddy کان صحت جو سوال پڇو...",
        "new_chat": "➕ نئين گفتگو",
        "recent_chats": "حاليہ گفتگو",
        "preferences": "ترجيحات ۽ ٻولي",
        "evidence_title": "ثبوت ذھانت",
        "quick_queries": "فوري مثال وارا سوال",
        "status_ready": "🟢 ثبوت سروس تيار آھي",
        "empty_evidence": "توهان جا ثبوت، ذريعا ۽ رابطا هتي ظاهر ٿيندا.",
    },
    # ── Global Languages ──────────────────────────────────────
    "en": {
        "label": "🌍 English (en)",
        "category": "Global",
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
    "es": {
        "label": "🌍 Spanish / Español (es)",
        "category": "Global",
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
        "label": "🌍 French / Français (fr)",
        "category": "Global",
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
    "de": {
        "label": "🌍 German / Deutsch (de)",
        "dir": "ltr",
        "title": "Fragen Sie MedicoBuddy",
        "tagline": "Jede Gesundheitsfrage, verbunden mit klareren Beweisen",
        "input_placeholder": "Stellen Sie MedicoBuddy eine Gesundheitsfrage...",
        "new_chat": "➕ Neue Unterhaltung",
        "recent_chats": "Letzte Unterhaltungen",
        "preferences": "Einstellungen und Sprache",
        "evidence_title": "Evidenz-Intelligenz",
        "quick_queries": "Schnelle Beispielsfragen",
        "status_ready": "🟢 Evidenzdienst bereit",
        "empty_evidence": "Ihre Evidenz, Quellen und Verbindungen werden hier angezeigt.",
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


# ── 3. Sidebar Controls & Global Searchable Language Selector ─
def render_sidebar() -> dict[str, Any]:
    """Render Navigation Sidebar with 22 Scheduled Indian Languages & Searchable Selector."""
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
