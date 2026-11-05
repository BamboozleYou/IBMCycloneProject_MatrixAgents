"""Page 1 — Cyclone Detection: scenario input, live map, wind/pressure charts."""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.components.kpi_row import render_kpi_row
from dashboard.components.map_builder import build_track_map
from dashboard.components.chroma_panel import render_similar_cyclones
from dashboard.components.theme import ACCENT, GREEN, RED, ORANGE, SURFACE, MUTED, imd_label

# ── Scenario presets ─────────────────────────────────────────────────────────
_PRESETS = {
    "Odisha VSCS": {
        "name": "Fani-2", "landfall": "Odisha Coast",
        "wind_kmh": 185, "radius_km": 130, "pop_at_risk_k": 450,
        "lat0": 19.5, "lon0": 87.5, "lat_land": 19.8, "lon_land": 85.8,
        "districts": [
            {"name": "Puri",           "lat": 19.81, "lon": 85.83},
            {"name": "Khurda",         "lat": 20.17, "lon": 85.61},
            {"name": "Jagatsinghpur",  "lat": 20.25, "lon": 86.17},
            {"name": "Kendrapara",     "lat": 20.50, "lon": 86.42},
            {"name": "Balasore",       "lat": 21.49, "lon": 86.93},
        ],
    },
    "Andhra SCS": {
        "name": "Hudhud-2", "landfall": "Visakhapatnam",
        "wind_kmh": 140, "radius_km": 90, "pop_at_risk_k": 280,
        "lat0": 17.0, "lon0": 84.5, "lat_land": 17.7, "lon_land": 83.3,
        "districts": [
            {"name": "Visakhapatnam", "lat": 17.69, "lon": 83.22},
            {"name": "Vizianagaram",  "lat": 18.12, "lon": 83.40},
            {"name": "Srikakulam",    "lat": 18.30, "lon": 83.90},
            {"name": "East Godavari", "lat": 17.00, "lon": 81.78},
            {"name": "West Godavari", "lat": 16.92, "lon": 81.37},
        ],
    },
    "Gujarat CS": {
        "name": "Vayu-2", "landfall": "Veraval",
        "wind_kmh": 100, "radius_km": 65, "pop_at_risk_k": 120,
        "lat0": 21.5, "lon0": 70.5, "lat_land": 20.9, "lon_land": 70.4,
        "districts": [
            {"name": "Gir Somnath",  "lat": 20.91, "lon": 70.36},
            {"name": "Junagadh",     "lat": 21.52, "lon": 70.46},
            {"name": "Porbandar",    "lat": 21.64, "lon": 69.61},
            {"name": "Amreli",       "lat": 21.60, "lon": 71.22},
            {"name": "Bhavnagar",    "lat": 21.76, "lon": 72.15},
        ],
    },
    "Manual": {},
}


def render() -> None:
    st.title("🌩 Cyclone Detection")
    kpi_slot = st.container()

    results  = st.session_state.get("last_results")
    scenario = st.session_state.get("scenario", {})
    st.divider()

    # ── Preset selector ───────────────────────────────────────────────────────
    col_p, col_rest = st.columns([1, 3])
    preset_name = col_p.selectbox("Scenario preset", list(_PRESETS.keys()))
    preset = _PRESETS[preset_name]

    with col_rest:
        c1, c2, c3 = st.columns(3)
        name     = c1.text_input("Cyclone name",          value=preset.get("name",     "My-Cyclone"))
        landfall = c2.text_input("Landfall location",     value=preset.get("landfall", "Coast"))
        wind_kmh = c3.number_input("Max wind (km/h)",     value=int(preset.get("wind_kmh", 150)), step=10)
        radius   = c1.number_input("Radius (km)",         value=int(preset.get("radius_km", 100)), step=10)
        pop_risk = c2.number_input("Population at risk (k)", value=int(preset.get("pop_at_risk_k", 200)), step=50)

    scenario_data = {
        "name": name, "landfall": landfall,
        "wind_kmh": wind_kmh, "radius_km": radius, "pop_at_risk_k": pop_risk,
        **{k: preset.get(k, d) for k, d in {
            "lat0": 18.0, "lon0": 86.0, "lat_land": 19.8, "lon_land": 85.8
        }.items()},
    }
    st.session_state["scenario"] = scenario_data

    with kpi_slot:
        render_kpi_row(results, scenario_data)

    # ── Map from weather_json if available ────────────────────────────────────
    weather_json = (results or {}).get("weather_json")
    chosen = ((results or {}).get("shelter_result") or {}).get("selected", [])
    fig_map = build_track_map(scenario_data, weather_json, chosen)

    # Animation slider
    n_steps = 12
    lats = np.linspace(scenario_data["lat0"], scenario_data["lat_land"], n_steps)
    lons = np.linspace(scenario_data["lon0"], scenario_data["lon_land"], n_steps)

    st.subheader("Track Animation")
    t_idx    = st.slider("Hour offset (T+h)", 0, (n_steps - 1) * 6, 0, step=6)
    step_idx = t_idx // 6

    # Update current-position trace
    fig_map.add_trace(go.Scattermapbox(
        lat=[lats[step_idx]], lon=[lons[step_idx]], mode="markers",
        marker=dict(size=14, color=ACCENT, symbol="circle"),
        name=f"T+{t_idx}h",
        hovertemplate=f"T+{t_idx}h<extra></extra>",
    ))

    st.plotly_chart(fig_map, use_container_width=True)

    # ── Wind gauge + forecast ─────────────────────────────────────────────────
    winds     = [wind_kmh * (0.6 + 0.4 * (i / (n_steps - 1))) for i in range(n_steps)]
    pressures = [1005 - 50 * (w / wind_kmh) for w in winds] if wind_kmh else [1005]*n_steps
    hours     = list(range(0, n_steps * 6, 6))

    col_g, col_l = st.columns([1, 2])
    with col_g:
        imd_lbl, imd_col = imd_label(winds[step_idx])
        st.subheader("Wind & IMD Intensity")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=winds[step_idx],
            delta={"reference": winds[0], "suffix": " km/h"},
            number={"suffix": " km/h", "font": {"size": 28}},
            title={"text": f"{imd_lbl} — T+{t_idx}h"},
            gauge={
                "axis": {"range": [0, 300], "tickcolor": MUTED},
                "bar":  {"color": imd_col},
                "bgcolor": SURFACE,
                "bordercolor": "#393939",
                "steps": [
                    {"range": [0, 63],   "color": "#161616"},
                    {"range": [63, 118], "color": "#1a2a1a"},
                    {"range": [118, 166],"color": "#2a2210"},
                    {"range": [166, 220],"color": "#2a1510"},
                    {"range": [220, 300],"color": "#200010"},
                ],
                "threshold": {"line": {"color": RED, "width": 3}, "value": wind_kmh},
            },
        ))
        fig_gauge.update_layout(paper_bgcolor=SURFACE, font_color="#f4f4f4",
                                height=280, margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_l:
        st.subheader("Wind & Pressure Forecast")
        fig_wp = go.Figure()
        fig_wp.add_trace(go.Scatter(x=hours, y=winds, name="Wind (km/h)",
                                    line=dict(color=ACCENT, width=2), mode="lines+markers"))
        fig_wp.add_trace(go.Scatter(x=hours, y=pressures, name="Pressure (hPa)", yaxis="y2",
                                    line=dict(color=GREEN, width=2, dash="dash"), mode="lines+markers"))
        fig_wp.add_vline(x=t_idx, line=dict(color=RED, dash="dot"), annotation_text="Now")
        fig_wp.update_layout(
            xaxis=dict(title="T+ hours", color=MUTED),
            yaxis=dict(title="Wind km/h", color=ACCENT),
            yaxis2=dict(title="Pressure hPa", overlaying="y", side="right", color=GREEN),
            paper_bgcolor=SURFACE, plot_bgcolor="#0a0a0a",
            font=dict(color="#f4f4f4"), legend=dict(bgcolor=SURFACE),
            height=280, margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig_wp, use_container_width=True)
        st.caption("Illustrative intensity profile (model-derived)")

    # ── District risk bar ─────────────────────────────────────────────────────
    st.subheader("District Risk")
    if preset_name == "Manual":
        st.info("Select a named preset to see district risk scores.")
    else:
        import math
        import plotly.express as px
        preset_districts = preset.get("districts", [])
        lon_land = scenario_data["lon_land"]
        lat_land = scenario_data["lat_land"]
        R = 6371.0  # Earth radius km

        def _dist_km(lat1, lon1, lat2, lon2):
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            return R * 2 * math.asin(math.sqrt(a))

        district_names = [d["name"] for d in preset_districts]
        risk_scores = [
            round(100 * min(1, wind_kmh / 220) * math.exp(-_dist_km(d["lat"], d["lon"], lat_land, lon_land) / radius))
            for d in preset_districts
        ]
        fig_bar = px.bar(x=risk_scores, y=district_names, orientation="h",
                         labels={"x": "Risk Score", "y": "District"},
                         color=risk_scores,
                         color_continuous_scale=[[0, GREEN], [0.5, "#f1c21b"], [1, RED]])
        fig_bar.update_layout(paper_bgcolor=SURFACE, plot_bgcolor="#0a0a0a",
                              font=dict(color="#f4f4f4"), showlegend=False,
                              height=260, margin=dict(l=10,r=10,t=10,b=10),
                              coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Similar cyclones from ChromaDB ────────────────────────────────────────
    st.divider()
    similar = (results or {}).get("similar_cyclones")
    if similar is None:
        # Live query without running full pipeline
        try:
            import sys
            from pathlib import Path as _P
            sys.path.insert(0, str(_P(__file__).parent.parent.parent))
            from memory.chroma_store import ChromaStore
            store = ChromaStore()
            store.seed()
            imd_lbl2, _ = imd_label(wind_kmh)
            similar = store.retrieve(f"{imd_lbl2} {landfall} cyclone India", k=3)
        except Exception:
            similar = []
    render_similar_cyclones(similar or [])
render()
