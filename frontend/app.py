"""MedicoBuddy AI — Enterprise Multilingual Health Workstation (Main App Entry Point).

Product Name: MedicoBuddy AI
Tagline: Everyday health questions, connected to clearer evidence.
Target Population: Adults aged 18–65 with mild, short-duration concerns.
Architecture: Modular Streamlit Package (`frontend/`)
"""

from __future__ import annotations

import logging
import sys
import uuid
from pathlib import Path

import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from frontend.api_client import send_chat_message
from frontend.components.chat import (
    render_assistant_response,
    render_starter_cards,
)
from frontend.components.sidebar import render_sidebar
from frontend.localization import get_translation
from frontend.state import init_session_state

logger = logging.getLogger(__name__)

# ── 1. Page Configuration ─────────────────────────────────────
st.set_page_config(
    page_title="MedicoBuddy AI — Health Education Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 2. Inject Custom Theme CSS ─────────────────────────────────
THEME_CSS_PATH = PROJECT_ROOT / "frontend" / "styles" / "theme.css"
if THEME_CSS_PATH.exists():
    try:
        css_content = THEME_CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except Exception as exc:
        logger.warning("Could not load theme.css: %s", exc)

# ── 3. Centralized Session State Initialization ────────────────
init_session_state()

# ── 4. Render Sidebar (Language, Context, Status, Admin) ──────
selected_lang_code, text_dir = render_sidebar()

# Apply RTL layout if needed
if text_dir == "rtl":
    st.markdown("<style>.main { direction: rtl; text-align: right; }</style>", unsafe_allow_html=True)

# ── 5. Render Header / Brand Title ─────────────────────────────
title_text = get_translation(selected_lang_code, "title", "Ask MedicoBuddy AI")
tagline_text = get_translation(
    selected_lang_code, "tagline", "Everyday health questions, connected to clearer evidence."
)
st.markdown(f"## 🩺 {title_text}")
st.caption(tagline_text)
st.divider()

# ── 6. Render Starter Cards (Only before first message) ───────
starter_query = None
if len(st.session_state.messages) == 0:
    starter_query = render_starter_cards()
    st.divider()

# ── 7. Render Conversation History ─────────────────────────────
for idx, msg in enumerate(st.session_state.messages):
    role = msg.get("role", "user")
    with st.chat_message(role):
        if role == "user":
            st.markdown(msg.get("content", ""))
        elif role == "assistant":
            data = msg.get("data")
            if isinstance(data, dict):
                render_assistant_response(
                    data=data,
                    query_text=msg.get("query", ""),
                    req_id=msg.get("request_id", ""),
                    msg_idx=idx,
                )
            else:
                st.markdown(msg.get("content", ""))

# ── 8. Process Input (Pending button click or chat_input) ─────
active_user_query = None
active_parent_req_id = None

if st.session_state.pending_query:
    active_user_query = st.session_state.pending_query
    active_parent_req_id = st.session_state.pending_parent_request_id
    st.session_state.pending_query = None
    st.session_state.pending_parent_request_id = None
elif starter_query:
    active_user_query = starter_query
else:
    placeholder_text = get_translation(
        selected_lang_code, "placeholder", "Ask MedicoBuddy AI a health question in any language..."
    )
    user_input = st.chat_input(placeholder_text, key="ci_user_query")
    if user_input:
        active_user_query = user_input

# ── 9. Submit & Render Response ────────────────────────────────
if active_user_query:
    req_id = str(uuid.uuid4())

    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": active_user_query,
        "data": None,
        "query": active_user_query,
    })

    with st.chat_message("user"):
        st.markdown(active_user_query)

    with st.chat_message("assistant"):
        progress_placeholder = st.empty()
        progress_placeholder.info("🔄 Running GraphRAG retrieval & evidence validation...")

        user_ctx = st.session_state.get("user_context", {})

        payload = {
            "message": active_user_query,
            "audience_mode": "patient_education",
            "preferred_language": selected_lang_code,
            "parent_request_id": active_parent_req_id,
            "thread_id": st.session_state.thread_id,
            "age_range": user_ctx.get("age_range", "18_65"),
            "pregnancy_status": user_ctx.get("pregnancy_status", "unknown"),
            "chronic_conditions": user_ctx.get("chronic_conditions", []),
            "allergies": user_ctx.get("allergies", []),
            "current_medicines": user_ctx.get("current_medicines", []),
            "immunocompromised": user_ctx.get("immunocompromised", False),
            "region": user_ctx.get("region", "IN"),
            "consent_given": True,
        }

        # Send request to backend
        response_data = send_chat_message(payload)
        progress_placeholder.empty()

        # Render response
        msg_idx = len(st.session_state.messages)
        render_assistant_response(
            data=response_data,
            query_text=active_user_query,
            req_id=req_id,
            msg_idx=msg_idx,
        )

        # Append assistant message to history
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_data.get("summary", ""),
            "data": response_data,
            "request_id": req_id,
            "parent_request_id": active_parent_req_id,
            "query": active_user_query,
            "language": selected_lang_code,
        })
