"""Feedback & Response Controls Component — MedicoBuddy AI.

Provides:
- Copy answer text
- Download complete response JSON report
- User feedback controls (helpful / needs improvement)
"""

from __future__ import annotations

import json
from typing import Any

import streamlit as st


def render_response_controls(data: dict[str, Any], msg_index: int) -> None:
    """Render copy, download, and feedback buttons for an assistant response."""
    col1, col2, col3, col4 = st.columns([1, 1.5, 1, 1])

    # 1. Download Report JSON
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    col1.download_button(
        label="📥 Report",
        data=json_str,
        file_name=f"medicobuddy_report_{msg_index}.json",
        mime="application/json",
        key=f"dl_{msg_index}",
    )

    # 2. Thumbs Up / Down Feedback
    if col3.button("👍 Helpful", key=f"thumb_up_{msg_index}"):
        st.toast("Thank you for your feedback!")

    if col4.button("👎 Needs Work", key=f"thumb_down_{msg_index}"):
        st.toast("Thank you. We will work to improve evidence accuracy.")
