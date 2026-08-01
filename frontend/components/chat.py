"""Chat Workspace Component — MedicoBuddy AI.

Handles:
- Starter cards display before 1st message (Headache, Cold & Cough, Nausea, Digestive Discomfort, Fatigue, Hair & Scalp)
- Conversation history card rendering
- Structured 12-part response formatting (Safety Banner, Summary, Action Table, Plan, Avoid, Warning Signs, Follow-up Questions)
- Sticky chat composer
- Interactive quick-action follow-up buttons
"""

from __future__ import annotations

import html
import uuid
from typing import Any

import streamlit as st

from frontend.components.action_table import render_action_table
from frontend.components.evidence_drawer import render_evidence_drawer
from frontend.components.feedback import render_response_controls


# Starter card definitions matching exact spec requirements
STARTER_CARDS = [
    {
        "id": "starter_headache",
        "icon": "🤕",
        "title": "Headache",
        "subtitle": "Mild tension headache self-care steps",
        "query": "I have a mild tension headache since this morning. What evidence-based self-care steps can I take?",
    },
    {
        "id": "starter_cold",
        "icon": "🤧",
        "title": "Cold & Cough",
        "subtitle": "Sore throat & nasal congestion relief",
        "query": "I have a slight cold and sore throat for 2 days. What natural remedies and self-care measures help?",
    },
    {
        "id": "starter_nausea",
        "icon": "🤢",
        "title": "Nausea",
        "subtitle": "Post-meal stomach discomfort & queasiness",
        "query": "I am feeling mild nausea after eating lunch. What non-pharmacological comfort steps should I try?",
    },
    {
        "id": "starter_digestive",
        "icon": "🫄",
        "title": "Digestive Discomfort",
        "subtitle": "Bloating & mild indigestion care",
        "query": "What natural self-care approaches help relieve mild bloating and digestive indigestion?",
    },
    {
        "id": "starter_fatigue",
        "icon": "🥱",
        "title": "Fatigue",
        "subtitle": "Workplace tiredness & sleep hygiene",
        "query": "I feel persistent tiredness after work. What sleep hygiene and nutrition practices boost daily energy?",
    },
    {
        "id": "starter_hair",
        "icon": "💇",
        "title": "Hair & Scalp Care",
        "subtitle": "Stress-related hair fall self-care",
        "query": "What evidence-based self-care and nutrition measures help reduce stress-related hair fall?",
    },
]


def render_starter_cards() -> str | None:
    """Render contextual starter cards before the first message.

    Returns the query string if a card is clicked, otherwise None.
    """
    st.markdown("#### Select a health concern or type your question below:")
    cols = st.columns(3)

    clicked_query = None
    for idx, card in enumerate(STARTER_CARDS):
        c = cols[idx % 3]
        btn_text = f"{card['icon']} **{card['title']}**\n\n_{card['subtitle']}_"
        if c.button(btn_text, key=f"btn_starter_{card['id']}", use_container_width=True):
            clicked_query = card["query"]

    return clicked_query


def render_safety_banner(safety_status: str, triage_outcome: str = "") -> None:
    """Render safety status banner in appropriate color."""
    status_lower = safety_status.lower()
    triage_lower = triage_outcome.lower()

    if "urgent" in status_lower or "emergency" in status_lower or triage_lower in ("urgent_care", "emergency"):
        st.markdown(
            f"""<div class="safety-banner-urgent">
              ⚠️ <b>URGENT MEDICAL EVALUATION ADVISED</b>: {html.escape(safety_status)}
            </div>""",
            unsafe_allow_html=True,
        )
    elif "warning" in status_lower or "professional" in status_lower:
        st.markdown(
            f"""<div class="safety-banner-warning">
              ⚠️ <b>PROFESSIONAL REVIEW ADVISED</b>: {html.escape(safety_status)}
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div class="safety-banner-self-care">
              ℹ️ <b>Safety Guidance Mode:</b> {html.escape(safety_status)}
            </div>""",
            unsafe_allow_html=True,
        )


def render_assistant_response(data: dict[str, Any], query_text: str = "", req_id: str = "", msg_idx: int = 0) -> None:
    """Render full structured 12-part assistant response."""
    if not isinstance(data, dict):
        st.error("Invalid response format received from backend.")
        return

    # 1. Safety Status Banner
    safety_status = data.get("safety_status", "SELF_CARE_INFORMATION")
    triage_outcome = str(data.get("triage_outcome", ""))
    render_safety_banner(safety_status, triage_outcome)

    # 2. What this applies to + Plain-Language Summary
    applies = data.get("what_this_applies_to", "")
    if applies:
        st.caption(f"🎯 **Scope:** {applies}")

    summary_text = data.get("summary", "")
    if summary_text:
        st.markdown("### Summary Guidance")
        st.markdown(summary_text)

    # 3. Responsive Action Table
    action_rows = data.get("action_table", [])
    if action_rows:
        render_action_table(action_rows)

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
            if isinstance(a, dict):
                p_name = a.get("practice", "")
                p_desc = a.get("description", "")
                e_label = a.get("evidence_label", "traditional_use_only").replace("_", " ").title()
                st.markdown(f"**{p_name}** `[{e_label}]`: {p_desc}")

    # 6. General Self-Care Education
    gen_edu = data.get("general_self_care_education", "")
    if gen_edu:
        st.markdown("### General Self-Care Education")
        st.info(gen_edu)

    # 7. Implementation Plan
    impl = data.get("implementation_plan", {})
    if impl and isinstance(impl, dict) and any(str(v).strip() for v in impl.values() if v):
        st.markdown("### Implementation Plan")
        c1, c2, c3 = st.columns(3)
        now_t = impl.get("now", "")
        next6_t = impl.get("next_6_to_12_hours", "")
        next24_t = impl.get("next_24_to_48_hours", "")
        if now_t:
            c1.metric("Now", now_t[:75] + ("..." if len(now_t) > 75 else ""))
        if next6_t:
            c2.metric("Next 6–12 Hours", next6_t[:75] + ("..." if len(next6_t) > 75 else ""))
        if next24_t:
            c3.metric("Next 24–48 Hours", next24_t[:75] + ("..." if len(next24_t) > 75 else ""))

    # 8. Things to Avoid
    avoid = data.get("things_to_avoid", [])
    if avoid:
        st.markdown("### Things to Avoid")
        for av in avoid:
            st.write(f"- 🚫 {av}")

    # 9. Warning Signs & When to Seek Care
    when_seek = data.get("when_to_seek_care", []) or data.get("warning_signs", [])
    if when_seek:
        st.markdown("### Warning Signs — When to Seek Care")
        for cond in when_seek:
            st.write(f"- ⚠️ {cond}")

    # 10. Evidence Drawer (Collapsible)
    render_evidence_drawer(data, req_id)

    # 11. Targeted Follow-up Question
    follow_up = data.get("follow_up_question") or data.get("targeted_follow_up", "")
    if follow_up:
        st.markdown(f"❓ **Clarifying Question:** {follow_up}")

    # 12. Interactive Follow-up Actions (Structured objects)
    quick_actions = data.get("quick_actions", [])
    chips = data.get("quick_action_chips", [])

    action_items: list[dict[str, str]] = []
    if quick_actions:
        for qa in quick_actions:
            if isinstance(qa, dict):
                action_items.append({
                    "label": qa.get("label", ""),
                    "standalone_query": qa.get("standalone_query", qa.get("label", "")),
                })
            elif isinstance(qa, str):
                action_items.append({"label": qa, "standalone_query": qa})
    elif chips:
        for chip in chips:
            if isinstance(chip, dict):
                action_items.append({
                    "label": chip.get("label", ""),
                    "standalone_query": chip.get("standalone_query", chip.get("label", "")),
                })
            elif isinstance(chip, str):
                action_items.append({"label": chip, "standalone_query": chip})

    if action_items:
        st.markdown("### 💬 Suggested Follow-up Actions")
        curr_req_id = req_id or str(uuid.uuid4())
        for index, item in enumerate(action_items):
            label = item.get("label", "")
            standalone_query = item.get("standalone_query", label)
            if not label:
                continue
            if st.button(
                label,
                key=f"btn_followup_{msg_idx}_{index}_{curr_req_id[:8]}",
                use_container_width=True,
            ):
                st.session_state.pending_query = standalone_query
                st.session_state.pending_parent_request_id = curr_req_id
                st.rerun()

    # Educational Notice & Feedback Controls
    st.divider()
    st.caption(
        "Educational-use notice: MedicoBuddy AI provides evidence-grounded general self-care education for adults aged 18–65. "
        "It does not diagnose, prescribe, recommend medicines, or replace professional medical evaluation."
    )
    render_response_controls(data, msg_idx)
