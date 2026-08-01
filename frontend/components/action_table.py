"""Action Table Component — MedicoBuddy AI.

Renders responsive HTML action table with exact column structure:
| Guidance | What May Help | How to Follow | Duration | Evidence | Cautions | Seek Care If |

INTEGRITY CONTRACT:
- Never substitutes fake fallback text when backend fields are missing.
- Escapes all HTML to prevent injection vulnerabilities.
"""

from __future__ import annotations

import html
from typing import Any

import streamlit as st


def render_action_table(action_rows: list[dict[str, Any]]) -> None:
    """Render 7-column responsive action table."""
    if not action_rows:
        return

    st.markdown("### Responsive Action Table")

    table_html = """
    <div class="action-table-container">
    <table class="action-table">
      <thead>
        <tr>
          <th>Guidance</th>
          <th>What May Help</th>
          <th>How to Follow</th>
          <th>Duration</th>
          <th>Evidence</th>
          <th>Cautions</th>
          <th>Seek Care If</th>
        </tr>
      </thead>
      <tbody>
    """

    for r in action_rows:
        if not isinstance(r, dict):
            continue

        # Extract values without substituting fake defaults
        g_lens = html.escape(str(r.get("guidance_lens", "") or ""))
        w_help = html.escape(str(r.get("what_may_help", "") or ""))
        h_follow = html.escape(str(r.get("how_to_follow", "") or ""))
        freq = html.escape(str(r.get("frequency_duration", "") or ""))
        e_str = html.escape(str(r.get("evidence_strength", r.get("evidence_level", "")) or ""))
        caut = html.escape(str(r.get("cautions", r.get("important_cautions", "")) or ""))
        seek = html.escape(str(r.get("stop_and_seek_care_if", "") or ""))

        table_html += f"""
        <tr>
          <td><b>{g_lens}</b></td>
          <td>{w_help}</td>
          <td>{h_follow}</td>
          <td>{freq}</td>
          <td>{e_str}</td>
          <td>{caut}</td>
          <td>{seek}</td>
        </tr>
        """

    table_html += """
      </tbody>
    </table>
    </div>
    """

    st.markdown(table_html, unsafe_allow_html=True)
