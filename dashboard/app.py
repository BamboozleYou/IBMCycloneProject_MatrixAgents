"""CycloneShield-Q · Command Centre Dashboard (6-page, st.navigation)."""
from __future__ import annotations
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.components.theme import inject_css, LAYOUT_ARGS

st.set_page_config(page_title="CycloneShield-Q", **LAYOUT_ARGS)
inject_css()

# ── Navigation ────────────────────────────────────────────────────────────────
pg = st.navigation(
    {
        "Operations": [
            st.Page("views/p1_detection.py",  title="🌩 Cyclone Detection",    default=True),
            st.Page("views/p2_pipeline.py",   title="🤖 Agent Pipeline"),
            st.Page("views/p3_quantum.py",    title="⚛ Quantum Optimiser"),
            st.Page("views/p4_approval.py",   title="✅ Evacuation & Approval"),
        ],
        "Governance": [
            st.Page("views/p5_audit.py",      title="📋 Audit & Costs"),
            st.Page("views/p6_status.py",     title="⚙️ System Status"),
        ],
    }
)

# Sidebar footer
with st.sidebar:
    st.divider()
    st.markdown("**CycloneShield-Q**  \nTeam Matrix Agents")
    st.caption("Prototype · IBM Hackathon")

pg.run()
