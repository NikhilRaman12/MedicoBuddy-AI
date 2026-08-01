"""MedicoBuddy AI — Comprehensive Multilingual Registry & Localization Module.

Supports Indian regional and international languages with full UI text translation
and Right-To-Left (RTL) text direction flags.
"""

from __future__ import annotations

from typing import Any

# Supported language registry
LANGUAGES: dict[str, dict[str, Any]] = {
    "auto": {
        "label": "🌐 Auto-detect Language",
        "dir": "ltr",
        "title": "Ask MedicoBuddy AI",
        "tagline": "Everyday health questions, connected to clearer evidence.",
        "placeholder": "Ask a health question in any language...",
        "new_chat": "New Conversation",
        "user_context": "User Health Context",
        "starter_title": "Select a health concern or type your question below:",
    },
    "en": {
        "label": "🇬🇧 English",
        "dir": "ltr",
        "title": "Ask MedicoBuddy AI",
        "tagline": "Everyday health questions, connected to clearer evidence.",
        "placeholder": "Ask a health question...",
        "new_chat": "New Conversation",
        "user_context": "User Health Context",
        "starter_title": "Select a health concern or type your question below:",
    },
    "hi": {
        "label": "🇮🇳 Hindi / हिंदी",
        "dir": "ltr",
        "title": "MedicoBuddy AI से पूछें",
        "tagline": "हर स्वास्थ्य प्रश्न, स्पष्ट साक्ष्यों से जुड़ा।",
        "placeholder": "स्वास्थ्य संबंधी प्रश्न पूछें...",
        "new_chat": "नया प्रश्न",
        "user_context": "उपयोगकर्ता स्वास्थ्य संदर्भ",
        "starter_title": "स्वास्थ्य विषय चुनें या नीचे अपना प्रश्न लिखें:",
    },
    "te": {
        "label": "🇮🇳 Telugu / తెలుగు",
        "dir": "ltr",
        "title": "MedicoBuddy AI ని అడగండి",
        "tagline": "ప్రతి ఆరోగ్య ప్రశ్న, స్పష్టమైన ఆధారాలతో అనుసంధానించబడింది।",
        "placeholder": "ఆరోగ్య ప్రశ్న అడగండి...",
        "new_chat": "కొత్త సంభాషణ",
        "user_context": "ఆరోగ్య సమాచారం",
        "starter_title": "ఆరోగ్య అంశాన్ని ఎంచుకోండి లేదా మీ ప్రశ్నను క్రింద టైప్ చేయండి:",
    },
    "ta": {
        "label": "🇮🇳 Tamil / தமிழ்",
        "dir": "ltr",
        "title": "MedicoBuddy AI யிடம் கேட்கவும்",
        "tagline": "ஒவ்வொரு சுகாதார கேள்வியும் தெளிவான ஆதாரங்களுடன் இணைக்கப்பட்டுள்ளது।",
        "placeholder": "சுகாதார கேள்வி கேட்கவும்...",
        "new_chat": "புதிய உரையாடல்",
        "user_context": "சுகாதார சூழல்",
        "starter_title": "ஒரு தலைப்பைத் தேர்ந்தெடுக்கவும் அல்லது உங்கள் கேள்வியை கீழே தட்டச்சு செய்யவும்:",
    },
    "bn": {
        "label": "🇮🇳 Bengali / বাংলা",
        "dir": "ltr",
        "title": "MedicoBuddy AI-কে জিজ্ঞাসা করুন",
        "tagline": "প্রতিটি স্বাস্থ্য প্রশ্ন, স্পষ্ট প্রমাণের সাথে যুক্ত।",
        "placeholder": "স্বাস্থ্য বিষয়ক প্রশ্ন জিজ্ঞাসা করুন...",
        "new_chat": "নতুন কথোপকথন",
        "user_context": "ব্যবহারকারীর স্বাস্থ্য তথ্য",
        "starter_title": "একটি বিষয় নির্বাচন করুন বা নিচে আপনার প্রশ্ন টাইপ করুন:",
    },
    "mr": {
        "label": "🇮🇳 Marathi / मराठी",
        "dir": "ltr",
        "title": "MedicoBuddy AI ला विचारा",
        "tagline": "प्रत्येक आरोग्य प्रश्न, स्पष्ट पुराव्यांशी जोडलेला।",
        "placeholder": "आरोग्य प्रश्न विचारा...",
        "new_chat": "नवीन संभाषण",
        "user_context": "आरोग्य माहिती",
        "starter_title": "विषय निवडा किंवा खाली तुमचा प्रश्न टाइप करा:",
    },
    "gu": {
        "label": "🇮🇳 Gujarati / ગુજરાતી",
        "dir": "ltr",
        "title": "MedicoBuddy AI ને પૂછો",
        "tagline": "દરેક આરોગ્ય પ્રશ્ન, સ્પષ્ટ પુરાવા સાથે જોડાયેલ.",
        "placeholder": "આરોગ્ય પ્રશ્ન પૂછો...",
        "new_chat": "નવી વાતચીત",
        "user_context": "આરોગ્ય માહિતી",
        "starter_title": "વિષય પસંદ કરો અથવા નીચે તમારો પ્રશ્ન લખો:",
    },
    "kn": {
        "label": "🇮🇳 Kannada / ಕನ್ನಡ",
        "dir": "ltr",
        "title": "MedicoBuddy AI ನನ್ನು ಕೇಳಿ",
        "tagline": "ಪ್ರತಿಯೊಂದು ಆರೋಗ್ಯ ಪ್ರಶ್ನೆ, ಸ್ಪಷ್ಟ ಸಾಕ್ಷ್ಯಗಳೊಂದಿಗೆ ಸಂಪರ್ಕ ಹೊಂದಿದೆ.",
        "placeholder": "ಆರೋಗ್ಯ ಪ್ರಶ್ನೆ ಕೇಳಿ...",
        "new_chat": "ಹೊಸ ಸಂಭಾಷಣೆ",
        "user_context": "ಆರೋಗ್ಯ ಮಾಹಿತಿ",
        "starter_title": "ವಿಷಯವನ್ನು ಆಯ್ಕೆಮಾಡಿ ಅಥವಾ ಕೆಳಗೆ ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ:",
    },
    "ml": {
        "label": "🇮🇳 Malayalam / മലയാളം",
        "dir": "ltr",
        "title": "MedicoBuddy AI-യോട് ചോദിക്കുക",
        "tagline": "ഓരോ ആരോഗ്യ ചോദ്യവും വ്യക്തമായ തെളിവുകളുമായി ബന്ധപ്പെട്ടിരിക്കുന്നു.",
        "placeholder": "ആരോഗ്യ ചോദ്യം ചോദിക്കുക...",
        "new_chat": "പുതിയ സംഭാഷണം",
        "user_context": "ആരോഗ്യ വിവരങ്ങൾ",
        "starter_title": "ഒരു വിഷയം തിരഞ്ഞെടുക്കുക അല്ലെങ്കിൽ ചോദ്യം ടൈപ്പ് ചെയ്യുക:",
    },
    "pa": {
        "label": "🇮🇳 Punjabi / ਪੰਜਾਬੀ",
        "dir": "ltr",
        "title": "MedicoBuddy AI ਨੂੰ ਪੁੱਛੋ",
        "tagline": "ਹਰ ਸਿਹਤ ਸਵਾਲ, ਸਪਸ਼ਟ ਸਬੂਤਾਂ ਨਾਲ ਜੁੜਿਆ ਹੋਇਆ।",
        "placeholder": "ਸਿਹਤ ਸੰਬੰਧੀ ਸਵਾਲ ਪੁੱਛੋ...",
        "new_chat": "ਨਵੀਂ ਗੱਲਬਾਤ",
        "user_context": "ਸਿਹਤ ਜਾਣਕਾਰੀ",
        "starter_title": "ਕੋਈ ਵਿਸ਼ਾ ਚੁਣੋ ਜਾਂ ਹੇਠਾਂ ਆਪਣਾ ਸਵਾਲ ਲਿਖੋ:",
    },
    "or": {
        "label": "🇮🇳 Odia / ଓଡ଼ିଆ",
        "dir": "ltr",
        "title": "MedicoBuddy AI କୁ ପଚାରନ୍ତୁ",
        "tagline": "ପ୍ରତ୍ୟେକ ସ୍ୱାସ୍ଥ୍ୟ ପ୍ରଶ୍ନ, ସ୍ପଷ୍ଟ ପ୍ରମାଣ ସହିତ ଯୋଡି ହୋଇଛି |",
        "placeholder": "ସ୍ୱାସ୍ଥ୍ୟ ପ୍ରଶ୍ନ ପଚାରନ୍ତୁ...",
        "new_chat": "ନୂତନ କଥାବାର୍ତ୍ତା",
        "user_context": "ସ୍ୱାସ୍ଥ୍ୟ ସୂଚନା",
        "starter_title": "ଗୋଟିଏ ବିଷୟ ବାଛନ୍ତୁ କିମ୍ବା ତଳେ ପ୍ରଶ୍ନ ଲେଖନ୍ତୁ:",
    },
    "ur": {
        "label": "🇮🇳 Urdu / اردو",
        "dir": "rtl",
        "title": "MedicoBuddy AI سے پوچھیں",
        "tagline": "ہر صحت کا سوال، واضح شواہد سے جڑا ہوا۔",
        "placeholder": "صحت سے متعلق سوال پوچھیں...",
        "new_chat": "نئی گفتگو",
        "user_context": "صحت کی معلومات",
        "starter_title": "موضوع منتخب کریں یا نیچے اپنا سوال ٹائپ کریں:",
    },
    "es": {
        "label": "🇪🇸 Spanish / Español",
        "dir": "ltr",
        "title": "Consulte a MedicoBuddy AI",
        "tagline": "Preguntas de salud cotidianas, conectadas con evidencia clara.",
        "placeholder": "Haga una pregunta de salud...",
        "new_chat": "Nueva conversación",
        "user_context": "Contexto de salud",
        "starter_title": "Seleccione un tema o escriba su pregunta a continuación:",
    },
    "fr": {
        "label": "🇫🇷 French / Français",
        "dir": "ltr",
        "title": "Demandez à MedicoBuddy AI",
        "tagline": "Questions de santé du quotidien, liées à des preuves claires.",
        "placeholder": "Posez une question de santé...",
        "new_chat": "Nouvelle conversation",
        "user_context": "Contexte de santé",
        "starter_title": "Sélectionnez un sujet ou tapez votre question ci-dessous:",
    },
    "de": {
        "label": "🇩🇪 German / Deutsch",
        "dir": "ltr",
        "title": "Fragen Sie MedicoBuddy AI",
        "tagline": "Alltägliche Gesundheitsfragen, verknüpft mit klaren Belegen.",
        "placeholder": "Stellen Sie eine Gesundheitsfrage...",
        "new_chat": "Neues Gespräch",
        "user_context": "Gesundheitskontext",
        "starter_title": "Wählen Sie ein Thema oder geben Sie Ihre Frage unten ein:",
    },
    "ar": {
        "label": "🇸🇦 Arabic / العربية",
        "dir": "rtl",
        "title": "اسأل MedicoBuddy AI",
        "tagline": "أسئلة صحية يومية، مرتبطة بأدلة واضحة.",
        "placeholder": "اطرح سؤالاً صحياً...",
        "new_chat": "محادثة جديدة",
        "user_context": "السياق الصحي",
        "starter_title": "اختر موضوعاً أو اكتب سؤالك أدناه:",
    },
    "zh": {
        "label": "🇨🇳 Chinese / 中文",
        "dir": "ltr",
        "title": "咨询 MedicoBuddy AI",
        "tagline": "日常健康问题，关联清晰证据。",
        "placeholder": "提出健康问题...",
        "new_chat": "新对话",
        "user_context": "健康背景",
        "starter_title": "选择主题或在下方输入您的问题：",
    },
}


def get_translation(lang_code: str, key: str, default: str = "") -> str:
    """Retrieve localized string for language code."""
    lang_info = LANGUAGES.get(lang_code, LANGUAGES["en"])
    return str(lang_info.get(key, LANGUAGES["en"].get(key, default)))


def get_text_direction(lang_code: str) -> str:
    """Return 'rtl' or 'ltr' direction for text layout."""
    return LANGUAGES.get(lang_code, {}).get("dir", "ltr")
