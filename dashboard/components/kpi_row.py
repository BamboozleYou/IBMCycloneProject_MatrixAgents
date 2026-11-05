"""Shared KPI card row component."""
from __future__ import annotations
import sqlite3
from pathlib import Path

import streamlit as st

from dashboard.components.theme import imd_label

_COSTS_DB = Path(__file__).parent.parent.parent / "costs.db"


def kpi_card(label: str, value: str, sub: str = "") -> str:
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{sub_html}'
        f'</div>'
    )


def render_kpi_row(results: dict | None = None, scenario: dict | None = None) -> None:
    cd = (results or {}).get("cyclone_data", scenario or {})
    wj = (results or {}).get("weather_json", {})
    shelter_res = ((results or {}).get("shelter_result") or {})
    selected = shelter_res.get("selected", [shelter_res.get("best_shelter", "—")])
    shelter_str = ", ".join(selected) if selected else "—"
    pipeline = "✅ Complete" if results else "⏸ Not run"

    wind = float(wj.get("peak_wind_kmh") or cd.get("wind_kmh") or 0)
    imd_lbl, _ = imd_label(wind)
    imd_display = imd_lbl if wind else "—"
    confidence = wj.get("confidence", "—")
    conf_str = f"{confidence:.0%}" if isinstance(confidence, float) else "—"

    total_usd = 0.0
    try:
        if _COSTS_DB.exists():
            with sqlite3.connect(_COSTS_DB) as con:
                row = con.execute("SELECT SUM(usd_estimate) FROM costs").fetchone()
                total_usd = row[0] or 0.0
    except Exception:
        pass

    items = [
        ("Cyclone",        cd.get("name", "—"),                 ""),
        ("IMD Class",      imd_display,                         ""),
        ("Max Wind",       f"{wind:.0f} km/h" if wind else "—", ""),
        ("Landfall",       cd.get("landfall", "—"),              ""),
        ("T-minus",        f"{wj.get('time_to_landfall_h', '—')}h", "to landfall"),
        ("Shelter(s)",     shelter_str,                          "QAOA optimal"),
        ("Confidence",     conf_str,                             "model output"),
        ("LLM Cost",       f"${total_usd:.4f}",                  "cumulative"),
    ]
    row1 = st.columns(4)
    row2 = st.columns(4)
    all_cols = row1 + row2
    for col, (lbl, val, sub) in zip(all_cols, items):
        col.markdown(kpi_card(lbl, val, sub), unsafe_allow_html=True)
