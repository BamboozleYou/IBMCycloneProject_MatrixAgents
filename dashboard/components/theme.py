"""Shared theme constants and CSS for CycloneShield-Q dashboard."""
from __future__ import annotations
import streamlit as st

# ── Colour palette ───────────────────────────────────────────────────────────
BG       = "#0d0d0d"
SURFACE  = "#161616"
BORDER   = "#393939"
TEXT     = "#f4f4f4"
MUTED    = "#8d8d8d"
ACCENT   = "#0F62FE"   # IBM Blue
GREEN    = "#42be65"
YELLOW   = "#f1c21b"
ORANGE   = "#ff832b"
RED      = "#da1e28"
PURPLE   = "#6929c4"

# IMD scale: (max_wind_kmh, label, colour)
IMD_SCALE = [
    (63,  "Depression",                      GREEN),
    (89,  "Deep Depression",                 "#74c469"),
    (117, "Cyclonic Storm",                  YELLOW),
    (166, "Severe Cyclonic Storm",           ORANGE),
    (221, "Very Severe Cyclonic Storm",      RED),
    (260, "Extremely Severe Cyclonic Storm", "#a61f1f"),
    (999, "Super Cyclonic Storm",            PURPLE),
]


def imd_label(wind_kmh: float) -> tuple[str, str]:
    for threshold, label, colour in IMD_SCALE:
        if wind_kmh <= threshold:
            return label, colour
    return IMD_SCALE[-1][1], IMD_SCALE[-1][2]


# ── Inject CSS ────────────────────────────────────────────────────────────────
def inject_css() -> None:
    st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{background:{BG};}}
[data-testid="stSidebar"] {{background:{SURFACE}; border-right:1px solid {BORDER};}}
.kpi-card {{
    background:{SURFACE}; border:1px solid {BORDER}; border-radius:6px;
    padding:14px 18px; margin-bottom:8px;
}}
.kpi-label {{font-size:11px; color:{MUTED}; text-transform:uppercase; letter-spacing:.06em; margin-bottom:2px;}}
.kpi-value {{font-size:22px; font-weight:700; color:{TEXT};}}
.kpi-sub   {{font-size:12px; color:#a8a8a8; margin-top:2px;}}
.section-head {{font-size:13px; font-weight:600; color:{MUTED}; text-transform:uppercase; letter-spacing:.08em; margin:18px 0 8px 0;}}
.similar-card {{
    background:{SURFACE}; border-left:3px solid {ACCENT};
    border-radius:4px; padding:10px 14px; margin-bottom:8px;
}}
.tag {{display:inline-block; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; margin-right:4px;}}
</style>
""", unsafe_allow_html=True)


LAYOUT_ARGS = dict(page_icon="🌀", layout="wide")
