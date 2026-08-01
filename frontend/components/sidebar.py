"""Sidebar Component — MedicoBuddy AI.

Collapsible sidebar containing:
- Logo & Tagline
- New Conversation button
- Searchable Multilingual Selector (18 languages)
- User Context inputs with exact enum mapping (Unknown / Not Pregnant must never map to pregnant)
- Accessibility preferences & Privacy controls
- Admin Diagnostics expander
"""

from __future__ import annotations

import streamlit as st

from frontend.components.status import render_admin_diagnostics, render_status_badge
from frontend.localization import LANGUAGES
from frontend.state import reset_conversation


def render_sidebar() -> tuple[str, str]:
    """Render sidebar and return (selected_language, selected_direction)."""
    with st.sidebar:
        # Header / Brand
        st.markdown(
            """
            <div class="mb-brand-header">
              <h2 class="mb-brand-title">🩺 MedicoBuddy AI</h2>
              <div class="mb-brand-tagline">Everyday health questions, connected to clearer evidence.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Status badge (reads actual backend ready state)
        render_status_badge()
        st.write("")

        # 1. New Conversation Button
        if st.button("➕ New Conversation", use_container_width=True, key="btn_new_chat"):
            reset_conversation()
            st.rerun()

        st.divider()

        # 2. Searchable Multilingual Selector
        lang_options = list(LANGUAGES.keys())
        lang_labels = [LANGUAGES[k]["label"] for k in lang_options]

        current_lang = st.session_state.get("selected_language", "auto")
        curr_idx = lang_options.index(current_lang) if current_lang in lang_options else 0

        selected_label = st.selectbox(
            "🌐 Language / 🇮🇳 ભાષા / 🇮🇳 భాష",
            options=lang_labels,
            index=curr_idx,
            key="sb_language_picker",
        )
        selected_lang_code = lang_options[lang_labels.index(selected_label)]
        st.session_state.selected_language = selected_lang_code
        text_dir = LANGUAGES.get(selected_lang_code, {}).get("dir", "ltr")

        st.divider()

        # 3. User Health Context Section
        with st.expander("👤 User Health Context", expanded=False):
            # Age Group (Exact enum mapping)
            age_display_map = {
                "Adults 18–65 (Target Population)": "18_65",
                "Youth (Under 18)": "under_18",
                "Seniors (Over 65)": "over_65",
            }
            selected_age_label = st.selectbox(
                "Age Group",
                options=list(age_display_map.keys()),
                index=0,
                key="sb_age_group",
            )
            age_enum = age_display_map[selected_age_label]

            # Pregnancy / Breastfeeding Status (Unknown/Not Pregnant MUST never map to pregnant)
            preg_display_map = {
                "Not Pregnant / Not Applicable": "not_pregnant",
                "Currently Pregnant": "pregnant",
                "Currently Breastfeeding": "breastfeeding",
                "Unknown / Prefer not to say": "unknown",
            }
            selected_preg_label = st.selectbox(
                "Pregnancy / Breastfeeding Status",
                options=list(preg_display_map.keys()),
                index=0,
                key="sb_preg_status",
            )
            preg_enum = preg_display_map[selected_preg_label]

            # Chronic Conditions
            chronic_options = [
                "Hypertension", "Diabetes Type 2", "Asthma",
                "Thyroid Disorder", "GERD / Acid Reflux", "Kidney Disease",
            ]
            selected_conditions = st.multiselect(
                "Chronic Conditions (if any)",
                options=chronic_options,
                default=[],
                key="sb_chronic_cond",
            )

            # Update session state context dict
            st.session_state.user_context = {
                "age_range": age_enum,
                "pregnancy_status": preg_enum,
                "chronic_conditions": selected_conditions,
                "allergies": [],
                "current_medicines": [],
                "immunocompromised": False,
                "region": "IN",
            }

        # 4. Accessibility & Privacy Controls
        with st.expander("⚙️ Preferences & Privacy", expanded=False):
            high_contrast = st.checkbox("High Contrast Mode", value=False, key="chk_high_contrast")
            st.session_state.accessibility["high_contrast"] = high_contrast

            if st.button("🗑️ Clear Conversation History", key="btn_clear_history"):
                reset_conversation()
                st.rerun()

        # 5. Admin Diagnostics Expander
        render_admin_diagnostics()

    return selected_lang_code, text_dir
