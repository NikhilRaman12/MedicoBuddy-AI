"""MedicoBuddy AI — Centralized Session State Management Module."""

from __future__ import annotations

import uuid

import streamlit as st


def init_session_state() -> None:
    """Initialize all Streamlit session state keys with clean defaults.

    Centralized initialization prevents KeyError and widget key collision.
    """
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None

    if "pending_parent_request_id" not in st.session_state:
        st.session_state.pending_parent_request_id = None

    if "selected_language" not in st.session_state:
        st.session_state.selected_language = "auto"

    # User Context state with exact enum defaults
    if "user_context" not in st.session_state:
        st.session_state.user_context = {
            "age_range": "18_65",
            "pregnancy_status": "unknown",  # Must never default to pregnant
            "chronic_conditions": [],
            "allergies": [],
            "current_medicines": [],
            "immunocompromised": False,
            "region": "IN",
        }

    if "accessibility" not in st.session_state:
        st.session_state.accessibility = {
            "high_contrast": False,
            "font_size": "medium",
        }

    if "admin_mode" not in st.session_state:
        st.session_state.admin_mode = False


def reset_conversation() -> None:
    """Reset the current conversation thread."""
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.pending_query = None
    st.session_state.pending_parent_request_id = None
