"""CycloneShield-Q · Streamlit dashboard — Prototype demo data."""
from __future__ import annotations

import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Paths ──────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

_AUDIT_DB = _ROOT / "audit.db"
_COSTS_DB = _ROOT / "costs.db"

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CycloneShield-Q",
    page_icon="🌀",
    layout="wide",
)

# ── Shared card CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
.kpi-card {
    background: #161616;
    border: 1px solid #393939;
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 8px;
}
.kpi-label { font-size: 11px; color: #8d8d8d; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 2px; }
.kpi-value { font-size: 22px; font-weight: 700; color: #f4f4f4; }
.kpi-sub   { font-size: 12px; color: #a8a8a8; margin-top: 2px; }
.agent-card {
    background: #161616;
    border: 1px solid #393939;
    border-radius: 6px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.status-done    { color: #42be65; font-weight: 600; }
.status-running { color: #f1c21b; font-weight: 600; }
.status-idle    { color: #6f6f6f; }
.flow-node      { display:inline-block; padding:6px 14px; border-radius:20px; font-size:13px; font-weight:600; margin:0 4px; }
.flow-arrow     { color:#8d8d8d; font-size:18px; }
</style>
""", unsafe_allow_html=True)

# ── Provider status ─────────────────────────────────────────────────────────
def _key_set(env: str) -> bool:
    v = os.environ.get(env, "")
    return bool(v) and not v.startswith("your_")

_PROVIDERS = {
    "Granite (watsonx)": _key_set("WATSONX_API_KEY"),
    "Gemini":            _key_set("GEMINI_API_KEY"),
    "Groq":              _key_set("GROQ_API_KEY"),
}

# ── Scenario presets ────────────────────────────────────────────────────────
_PRESETS = {
    "Odisha Cat-3": {
        "name": "Fani-2", "category": 3, "landfall": "Odisha Coast",
        "wind_kmh": 185, "radius_km": 130, "pop_at_risk_k": 450,
        "lat0": 19.5, "lon0": 87.5, "lat_land": 19.8, "lon_land": 85.8,
    },
    "Andhra Cat-2": {
        "name": "Hudhud-2", "category": 2, "landfall": "Visakhapatnam",
        "wind_kmh": 140, "radius_km": 90, "pop_at_risk_k": 280,
        "lat0": 17.0, "lon0": 84.5, "lat_land": 17.7, "lon_land": 83.3,
    },
    "Gujarat Cat-1": {
        "name": "Vayu-2", "category": 1, "landfall": "Veraval",
        "wind_kmh": 100, "radius_km": 65, "pop_at_risk_k": 120,
        "lat0": 21.5, "lon0": 70.5, "lat_land": 20.9, "lon_land": 70.4,
    },
    "Manual": None,
}

_CAT_COLOUR = {1: "#42be65", 2: "#f1c21b", 3: "#ff832b", 4: "#da1e28", 5: "#6929c4"}

# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🌀 CycloneShield-Q")
    st.markdown("**Team Matrix Agents**")
    st.divider()

    page = st.radio(
        "Navigate",
        ["🌩 Cyclone Detection", "🤖 Agent Pipeline", "⚛ Quantum Optimiser", "✅ Approval & Logs"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**LLM Providers**")
    for pname, online in _PROVIDERS.items():
        icon = "🟢" if online else "🔴"
        st.markdown(f"{icon} {pname}")

    st.divider()
    st.caption("Prototype demo data")

# ══════════════════════════════════════════════════════════════════════════
# HELPERS — KPI row
# ══════════════════════════════════════════════════════════════════════════
def _kpi_card(label: str, value: str, sub: str = "") -> str:
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{sub_html}'
        f'</div>'
    )


def _render_kpi_row(results: dict | None, scenario: dict | None = None) -> None:
    cd = (results or {}).get("cyclone_data", scenario or {})
    shelter = ((results or {}).get("shelter_result") or {}).get("best_shelter", "—")
    pipeline = "✅ Complete" if results else "⏸ Not run"

    # cost
    total_usd = 0.0
    try:
        if _COSTS_DB.exists():
            with sqlite3.connect(_COSTS_DB) as con:
                row = con.execute("SELECT SUM(usd_estimate) FROM costs").fetchone()
                total_usd = row[0] or 0.0
    except Exception:
        pass

    cols = st.columns(8)
    items = [
        ("Cyclone",      cd.get("name", "—"),                  ""),
        ("Category",     f"Cat-{cd.get('category', '—')}",     ""),
        ("Max Wind",     f"{cd.get('wind_kmh', '—')} km/h",    ""),
        ("Landfall",     cd.get("landfall", "—"),               ""),
        ("Pop. at Risk", f"{cd.get('pop_at_risk_k', '—')} k",  ""),
        ("Shelter",      shelter,                               "QAOA optimal"),
        ("Pipeline",     pipeline,                              ""),
        ("LLM Cost",     f"${total_usd:.4f}",                   "cumulative"),
    ]
    for col, (lbl, val, sub) in zip(cols, items):
        col.markdown(_kpi_card(lbl, val, sub), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE 1 — Cyclone Detection
# ══════════════════════════════════════════════════════════════════════════
if page == "🌩 Cyclone Detection":
    st.title("🌩 Cyclone Detection")

    results = st.session_state.get("last_results")
    _render_kpi_row(results)
    st.divider()

    # --- Preset + manual inputs -----------------------------------------------
    col_p, col_rest = st.columns([1, 3])
    preset_name = col_p.selectbox("Scenario preset", list(_PRESETS.keys()))

    preset = _PRESETS[preset_name] or {}

    with col_rest:
        c1, c2, c3 = st.columns(3)
        name     = c1.text_input("Cyclone name",          value=preset.get("name",     "My-Cyclone"))
        category = c2.selectbox("Category", [1, 2, 3, 4, 5],
                                 index=preset.get("category", 3) - 1)
        landfall = c3.text_input("Landfall location",     value=preset.get("landfall", "Coast"))
        wind_kmh = c1.number_input("Max wind (km/h)",     value=preset.get("wind_kmh", 150), step=10)
        radius   = c2.number_input("Radius (km)",         value=preset.get("radius_km", 100), step=10)
        pop_risk = c3.number_input("Population at risk (k)", value=preset.get("pop_at_risk_k", 200), step=50)

    st.session_state["scenario"] = {
        "name": name, "category": category, "landfall": landfall,
        "wind_kmh": wind_kmh, "radius_km": radius, "pop_at_risk_k": pop_risk,
        **{k: preset.get(k, v) for k, v in {
            "lat0": 18.0, "lon0": 86.0, "lat_land": 19.8, "lon_land": 85.8
        }.items()},
    }

    # ── Derive track points from preset (or manual defaults) ─────────────────
    lat0     = preset.get("lat0", 18.0)
    lon0     = preset.get("lon0", 86.0)
    lat_land = preset.get("lat_land", 19.8)
    lon_land = preset.get("lon_land", 85.8)

    # 12-hour steps from current position to landfall
    n_steps = 12
    import numpy as np
    lats = np.linspace(lat0, lat_land, n_steps)
    lons = np.linspace(lon0, lon_land, n_steps)
    hours = list(range(0, n_steps * 6, 6))  # every 6 h

    # Wind profile: peak at landfall
    winds = [wind_kmh * (0.6 + 0.4 * (i / (n_steps - 1))) for i in range(n_steps)]
    # Pressure drops as wind rises
    pressures = [1005 - 50 * (w / wind_kmh) for w in winds]

    # ── Time slider ──────────────────────────────────────────────────────────
    st.subheader("Track Animation")
    t_idx = st.slider("Hour offset (T+h)", 0, (n_steps - 1) * 6, 0, step=6)
    step_idx = t_idx // 6

    # ── Map ──────────────────────────────────────────────────────────────────
    # Shelters near landfall
    from mcp.qaoa_shelter import DEMO_SHELTERS
    shelter_lats = [lat_land + 0.4*i - 0.8 for i in range(len(DEMO_SHELTERS))]
    shelter_lons = [lon_land + 0.3*i - 0.6 for i in range(len(DEMO_SHELTERS))]

    chosen_shelter = (
        (st.session_state.get("last_results") or {})
        .get("shelter_result", {})
        .get("best_shelter", DEMO_SHELTERS[-1]["name"])
    )

    fig_map = go.Figure()

    # Cone of uncertainty (filled polygon around track)
    cone_lats = list(lats) + list(lats[::-1]) + [lats[0]]
    cone_lons_hi = [lon + radius/222 for lon in lons]
    cone_lons_lo = [lon - radius/222 for lon in lons]
    cone_lons = cone_lons_hi + cone_lons_lo[::-1] + [cone_lons_hi[0]]
    fig_map.add_trace(go.Scattermapbox(
        lat=cone_lats, lon=cone_lons, fill="toself",
        fillcolor="rgba(15,98,254,0.15)", line=dict(width=0),
        name="Uncertainty cone", hoverinfo="skip",
    ))

    # Full track line
    fig_map.add_trace(go.Scattermapbox(
        lat=list(lats), lon=list(lons), mode="lines",
        line=dict(color="#0F62FE", width=2, dash="dot"),
        name="Forecast track", hovertemplate="Lat %{lat:.2f} Lon %{lon:.2f}<extra></extra>",
    ))

    # Visited track (up to current time)
    fig_map.add_trace(go.Scattermapbox(
        lat=list(lats[:step_idx+1]), lon=list(lons[:step_idx+1]), mode="lines+markers",
        line=dict(color="#0F62FE", width=3),
        marker=dict(size=7, color="#0F62FE"),
        name="Track (T+0…now)",
    ))

    # Current position
    fig_map.add_trace(go.Scattermapbox(
        lat=[lats[step_idx]], lon=[lons[step_idx]], mode="markers",
        marker=dict(size=18, color=_CAT_COLOUR.get(category, "#ff832b"), symbol="circle"),
        name=f"Position (T+{t_idx}h)",
        hovertemplate=f"<b>{name}</b> T+{t_idx}h<br>Wind {winds[step_idx]:.0f} km/h<extra></extra>",
    ))

    # Landfall marker
    fig_map.add_trace(go.Scattermapbox(
        lat=[lat_land], lon=[lon_land], mode="markers+text",
        marker=dict(size=16, color="#da1e28", symbol="star"),
        text=["Landfall"], textposition="top right",
        name="Landfall", hovertemplate=f"<b>Landfall</b><br>{landfall}<extra></extra>",
    ))

    # Impact radius circle (approximated as scatter ring)
    angles = list(range(0, 361, 5))
    r_deg = radius / 111.0
    circle_lats = [lat_land + r_deg * np.sin(a * np.pi / 180) for a in angles]
    circle_lons = [lon_land + r_deg * np.cos(a * np.pi / 180) for a in angles]

    fig_map.add_trace(go.Scattermapbox(
        lat=circle_lats, lon=circle_lons, mode="lines",
        line=dict(color="#ff832b", width=1, dash="dot"),
        name=f"Impact radius ({radius} km)", hoverinfo="skip",
    ))

    # Shelters
    for s, slat, slon in zip(DEMO_SHELTERS, shelter_lats, shelter_lons):
        is_chosen = s["name"] == chosen_shelter
        fig_map.add_trace(go.Scattermapbox(
            lat=[slat], lon=[slon], mode="markers+text",
            marker=dict(size=14 if is_chosen else 10,
                        color="#42be65" if is_chosen else "#8d8d8d"),
            text=[s["name"]], textposition="top right",
            name=s["name"],
            hovertemplate=f"<b>{s['name']}</b><br>Cap {s['capacity']} · Score {s['score']}<extra></extra>",
        ))

    fig_map.update_layout(
        mapbox=dict(style="open-street-map", center=dict(lat=(lat0+lat_land)/2, lon=(lon0+lon_land)/2), zoom=5),
        margin=dict(l=0, r=0, t=0, b=0), height=500,
        paper_bgcolor="#161616", plot_bgcolor="#161616",
        legend=dict(bgcolor="#161616", font=dict(color="#f4f4f4"), x=0, y=1),
        showlegend=True,
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # ── Gauges + line charts ──────────────────────────────────────────────────
    col_g, col_l = st.columns([1, 2])

    with col_g:
        st.subheader("Wind & Category")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=winds[step_idx],
            delta={"reference": winds[0], "suffix": " km/h"},
            number={"suffix": " km/h", "font": {"size": 28}},
            title={"text": f"Cat-{category} — T+{t_idx}h"},
            gauge={
                "axis": {"range": [0, 300], "tickcolor": "#8d8d8d"},
                "bar": {"color": _CAT_COLOUR.get(category, "#ff832b")},
                "bgcolor": "#161616",
                "bordercolor": "#393939",
                "steps": [
                    {"range": [0, 63],   "color": "#161616"},
                    {"range": [63, 118], "color": "#1a2a1a"},
                    {"range": [118, 166],"color": "#2a2210"},
                    {"range": [166, 220],"color": "#2a1510"},
                    {"range": [220, 300],"color": "#200010"},
                ],
                "threshold": {"line": {"color": "#da1e28", "width": 3}, "value": wind_kmh},
            },
        ))
        fig_gauge.update_layout(paper_bgcolor="#161616", font_color="#f4f4f4", height=280, margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_l:
        st.subheader("Wind & Pressure Forecast")
        fig_wp = go.Figure()
        fig_wp.add_trace(go.Scatter(
            x=hours, y=winds, name="Wind (km/h)", line=dict(color="#0F62FE", width=2),
            mode="lines+markers",
        ))
        fig_wp.add_trace(go.Scatter(
            x=hours, y=pressures, name="Pressure (hPa)", yaxis="y2",
            line=dict(color="#42be65", width=2, dash="dash"), mode="lines+markers",
        ))
        fig_wp.add_vline(x=t_idx, line=dict(color="#da1e28", dash="dot"), annotation_text="Now")
        fig_wp.update_layout(
            xaxis=dict(title="T+ hours", color="#8d8d8d"),
            yaxis=dict(title="Wind km/h", color="#0F62FE"),
            yaxis2=dict(title="Pressure hPa", overlaying="y", side="right", color="#42be65"),
            paper_bgcolor="#161616", plot_bgcolor="#0a0a0a",
            font=dict(color="#f4f4f4"), legend=dict(bgcolor="#161616"),
            height=280, margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig_wp, use_container_width=True)

    # ── District risk bar ─────────────────────────────────────────────────────
    st.subheader("District Risk")
    districts = ["Puri", "Khurda", "Jagatsinghpur", "Kendrapara", "Bhadrak", "Balasore"]
    risk_scores = [95, 88, 82, 70, 60, 45]
    fig_bar = px.bar(
        x=risk_scores, y=districts, orientation="h",
        labels={"x": "Risk Score", "y": "District"},
        color=risk_scores,
        color_continuous_scale=[[0, "#42be65"], [0.5, "#f1c21b"], [1, "#da1e28"]],
    )
    fig_bar.update_layout(
        paper_bgcolor="#161616", plot_bgcolor="#0a0a0a", font=dict(color="#f4f4f4"),
        showlegend=False, height=260, margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE 2 — Agent Pipeline
# ══════════════════════════════════════════════════════════════════════════
elif page == "🤖 Agent Pipeline":
    st.title("🤖 Agent Pipeline")

    results = st.session_state.get("last_results")
    scenario = st.session_state.get("scenario", {})
    _render_kpi_row(results, scenario)
    st.divider()

    # ── Flow diagram ─────────────────────────────────────────────────────────
    AGENTS_META = [
        ("Weather",    "weather_track",  "track_summary",  "Granite"),
        ("Impact",     "impact",         "impact_summary", "Gemini"),
        ("QAOA",       "qaoa_shelter",   "shelter_result", "Qiskit"),
        ("Evacuation", "evacuation",     "evacuation_plan","Groq"),
        ("Approval",   "hitl",           "pending_approval","Human"),
    ]

    done_keys = set(results.keys()) if results else set()

    def _node_colour(key: str) -> str:
        if results is None:
            return "#393939"
        if key in done_keys or (key == "hitl" and "pending_approval" in done_keys):
            return "#42be65"
        return "#393939"

    flow_html = '<div style="display:flex;align-items:center;flex-wrap:wrap;gap:6px;margin:10px 0 20px 0;">'
    for i, (label, key, res_key, model) in enumerate(AGENTS_META):
        bg = _node_colour(res_key)
        flow_html += (
            f'<span class="flow-node" style="background:{bg};color:#f4f4f4;">{label}</span>'
        )
        if i < len(AGENTS_META) - 1:
            flow_html += '<span class="flow-arrow">→</span>'
    flow_html += "</div>"
    st.markdown(flow_html, unsafe_allow_html=True)

    # ── Run button ────────────────────────────────────────────────────────────
    scenario_data = st.session_state.get("scenario") or {
        "name": "Demo-Alpha", "category": 3, "landfall": "Odisha Coast",
        "wind_kmh": 185, "radius_km": 130, "pop_at_risk_k": 450,
    }

    run_btn = st.button("▶ Run Pipeline", type="primary")

    if run_btn:
        progress = st.progress(0, "Initialising…")
        step_results: dict[str, tuple[str, str, float]] = {}  # key → (model, content, elapsed)

        try:
            from agents.supervisor import Supervisor
            import types

            sup = Supervisor()

            # Monkey-patch to capture per-agent timing
            orig = sup._run_agent_with_retries.__func__  # noqa: SLF001

            def _patched(self_inner, agent, input_text, extra_context=""):
                t0 = time.monotonic()
                res = orig(self_inner, agent, input_text, extra_context)
                elapsed = time.monotonic() - t0
                step_results[agent.name] = (agent.model, res, elapsed)
                return res

            sup._run_agent_with_retries = types.MethodType(_patched, sup)

            # Step-by-step progress
            progress.progress(10, "WeatherTrack…")
            run_results = sup.run(scenario_data)
            st.session_state["last_results"] = run_results
            st.session_state["step_results"] = step_results
            progress.progress(100, "Pipeline complete ✅")
            st.success("Pipeline complete — see Approval & Logs.")
        except Exception as exc:
            st.error(f"Pipeline error: {exc}")
            progress.progress(100)

    # ── Agent cards ────────────────────────────────────────────────────────────
    results = st.session_state.get("last_results")
    step_results = st.session_state.get("step_results", {})

    # Try to get token counts from costs.db for this run
    cost_map: dict[str, dict] = {}
    try:
        if _COSTS_DB.exists():
            with sqlite3.connect(_COSTS_DB) as con:
                rows = con.execute(
                    "SELECT agent, model, tokens_in, tokens_out FROM costs ORDER BY id DESC LIMIT 20"
                ).fetchall()
            for r in rows:
                if r[0] not in cost_map:
                    cost_map[r[0]] = {"model": r[1], "tokens_in": r[2], "tokens_out": r[3]}
    except Exception:
        pass

    if results is None:
        st.info("Run a scenario first.")
    else:
        output_map = {
            "weather_track": results.get("track_summary", ""),
            "impact":        results.get("impact_summary", ""),
            "qaoa_shelter":  str(results.get("shelter_result", "")),
            "evacuation":    results.get("evacuation_plan", ""),
        }
        for label, key, res_key, model_hint in AGENTS_META[:-1]:  # exclude HITL
            content = output_map.get(key, "")
            sr = step_results.get(key, (model_hint, content, 0.0))
            actual_model = sr[0] if sr[0] else model_hint
            elapsed = sr[2]
            cm = cost_map.get(key, {})
            tokens_in  = cm.get("tokens_in", "—")
            tokens_out = cm.get("tokens_out", "—")

            with st.expander(f"**{label}** · {actual_model}", expanded=bool(content)):
                mcol1, mcol2, mcol3 = st.columns(3)
                mcol1.metric("Tokens in",  tokens_in)
                mcol2.metric("Tokens out", tokens_out)
                mcol3.metric("Time",       f"{elapsed:.1f}s" if elapsed else "—")
                st.markdown(content or "_No output_")


# ══════════════════════════════════════════════════════════════════════════
# PAGE 3 — Quantum Optimiser
# ══════════════════════════════════════════════════════════════════════════
elif page == "⚛ Quantum Optimiser":
    st.title("⚛ Quantum Optimiser — QAOA vs Classical")

    results = st.session_state.get("last_results")
    scenario = st.session_state.get("scenario", {})
    _render_kpi_row(results, scenario)
    st.divider()

    from mcp.qaoa_shelter import DEMO_SHELTERS, _brute_force

    shelters = DEMO_SHELTERS
    classical = _brute_force(shelters)

    try:
        from mcp.qaoa_shelter import _qaoa
        quantum = _qaoa(shelters)
        qaoa_status = "✅ Ran on Qiskit Aer simulator"
    except Exception as exc:
        quantum = {
            "best_shelter": classical["best_shelter"],
            "method": "brute_force_fallback",
            "objective_value": classical["objective_value"],
        }
        qaoa_status = f"⚠️ Fallback ({exc.__class__.__name__}: {str(exc)[:60]})"

    match = quantum["best_shelter"] == classical["best_shelter"]

    # ── Metric cards ───────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("QAOA Best Shelter",      quantum["best_shelter"],   f"obj = {quantum['objective_value']:.0f}")
    c2.metric("Classical Best Shelter", classical["best_shelter"], f"obj = {classical['objective_value']:.0f}")
    c3.metric("Agreement", "✅ Match" if match else "❌ Differs")
    c4.metric("QAOA Method", quantum["method"])
    st.caption(qaoa_status)

    st.divider()

    col_left, col_right = st.columns(2)

    # ── Objective value bar chart ─────────────────────────────────────────────
    with col_left:
        st.subheader("Objective Value per Shelter")
        df_shelters = pd.DataFrame(shelters)
        df_shelters["objective"] = df_shelters["capacity"] * df_shelters["score"]
        df_shelters["chosen"] = df_shelters["name"] == quantum["best_shelter"]
        colours = ["#0F62FE" if c else "#393939" for c in df_shelters["chosen"]]

        fig_obj = go.Figure(go.Bar(
            x=df_shelters["name"],
            y=df_shelters["objective"],
            marker_color=colours,
            hovertemplate="%{x}<br>Objective: %{y:.0f}<extra></extra>",
        ))
        fig_obj.update_layout(
            paper_bgcolor="#161616", plot_bgcolor="#0a0a0a",
            font=dict(color="#f4f4f4"),
            xaxis=dict(tickangle=-25, color="#8d8d8d"),
            yaxis=dict(title="cap × score", color="#8d8d8d"),
            height=320, margin=dict(l=10, r=10, t=10, b=80),
        )
        st.plotly_chart(fig_obj, use_container_width=True)

    # ── Bitstring probability histogram ──────────────────────────────────────
    with col_right:
        st.subheader("QAOA Bitstring Distribution")
        import random, math
        random.seed(42)
        n = len(shelters)
        # Simulated probabilities — chosen shelter's bitstring gets highest weight
        chosen_idx = next(i for i, s in enumerate(shelters) if s["name"] == quantum["best_shelter"])
        bitstrings = []
        probs = []
        for i in range(n):
            bs = "0" * n
            bs = bs[:i] + "1" + bs[i+1:]
            bitstrings.append(bs)
            probs.append(0.5 if i == chosen_idx else random.uniform(0.05, 0.25))
        total = sum(probs)
        probs = [p / total for p in probs]

        fig_hist = go.Figure(go.Bar(
            x=bitstrings, y=probs,
            marker_color=["#0F62FE" if i == chosen_idx else "#393939" for i in range(n)],
            hovertemplate="%{x}<br>P=%{y:.3f}<extra></extra>",
        ))
        fig_hist.update_layout(
            paper_bgcolor="#161616", plot_bgcolor="#0a0a0a",
            font=dict(color="#f4f4f4"),
            xaxis=dict(title="Bitstring", color="#8d8d8d", tickangle=-25),
            yaxis=dict(title="Probability", color="#8d8d8d"),
            height=320, margin=dict(l=10, r=10, t=10, b=80),
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # ── QAOA circuit diagram (text representation) ─────────────────────────────
    st.subheader("QAOA Circuit (p=1)")
    try:
        from qiskit_algorithms import QAOA
        from qiskit_algorithms.optimizers import COBYLA
        from qiskit.primitives import Sampler
        from qiskit_optimization import QuadraticProgram
        from qiskit_optimization.converters import QuadraticProgramToQubo

        n = len(shelters)
        qp = QuadraticProgram(name="shelter_select")
        for i in range(n):
            qp.binary_var(name=f"x{i}")
        linear = {f"x{i}": -s["capacity"] * s["score"] for i, s in enumerate(shelters)}
        qp.minimize(linear=linear)
        qp.linear_constraint(linear={f"x{i}": 1 for i in range(n)}, sense="==", rhs=1, name="pick_one")

        conv = QuadraticProgramToQubo()
        qubo = conv.convert(qp)
        from qiskit_optimization.algorithms.minimum_eigen_optimizer import MinimumEigenOptimizer
        sampler = Sampler()
        qaoa_inst = QAOA(sampler=sampler, optimizer=COBYLA(), reps=1)
        circuit = qaoa_inst.ansatz
        st.code(str(circuit.draw(output="text")), language="text")
    except Exception as exc:
        # Textual fallback
        n = len(shelters)
        circuit_txt = f"q_0: ──H──Rz(γ)──Ry(β)──\n" + \
                      "\n".join(f"q_{i}: ──H──Rz(γ)──Ry(β)──" for i in range(1, n)) + \
                      f"\n\n(p=1, {n} qubits — {exc.__class__.__name__})"
        st.code(circuit_txt, language="text")

    # ── Shelter candidates table ───────────────────────────────────────────────
    st.subheader("Shelter Candidates")
    df_disp = pd.DataFrame(shelters).rename(columns={
        "name": "Shelter", "capacity": "Capacity", "score": "Suitability Score"
    })
    df_disp["Objective (cap×score)"] = df_disp["Capacity"] * df_disp["Suitability Score"]
    st.dataframe(df_disp, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE 4 — Approval & Logs
# ══════════════════════════════════════════════════════════════════════════
elif page == "✅ Approval & Logs":
    st.title("✅ Approval & Logs")

    results = st.session_state.get("last_results")
    scenario = st.session_state.get("scenario", {})
    _render_kpi_row(results, scenario)
    st.divider()

    # ── Evacuation plan approval ───────────────────────────────────────────────
    st.subheader("Human-in-the-Loop Approval")

    if results and results.get("pending_approval"):
        evac_plan = results.get("evacuation_plan", "No plan text available.")
        shelter   = results.get("shelter_result", {}).get("best_shelter", "—")
        cd        = results.get("cyclone_data", {})

        # SMS-style alert preview
        sms_text = (
            f"⚠️ CYCLONE ALERT: {cd.get('name','CYCLONE')} Cat-{cd.get('category','')} "
            f"approaching {cd.get('landfall','coast')}. "
            f"Evacuate NOW to {shelter}. Follow official routes. "
            f"Wind {cd.get('wind_kmh','?')} km/h. Stay safe. #DisasterAlert"
        )
        with st.container():
            st.markdown("**📱 SMS Alert Preview**")
            st.info(sms_text)

        st.warning("⏳ Evacuation plan is pending human approval.")
        with st.expander("📄 Evacuation Plan", expanded=True):
            st.markdown(evac_plan)

        approver = st.text_input("Approver name / ID", value="operator-1")
        col_a, col_r = st.columns(2)
        approve_btn = col_a.button("✅ Approve", type="primary")
        reject_btn  = col_r.button("❌ Reject")

        if approve_btn:
            from governance.audit import log_action
            log_action("supervisor", "evacuation_approved",
                       {"plan": evac_plan[:200]}, approved_by=approver)
            results["pending_approval"] = False
            st.session_state["last_results"] = results
            st.success(f"Plan approved by **{approver}** — logged to audit.")

        if reject_btn:
            from governance.audit import log_action
            log_action("supervisor", "evacuation_rejected",
                       {"plan": evac_plan[:200]}, approved_by=approver)
            results["pending_approval"] = False
            st.session_state["last_results"] = results
            st.error("Plan rejected and logged.")

    elif results and not results.get("pending_approval"):
        st.success("No pending approvals — all actions reviewed.")
    else:
        st.info("Run a scenario first (Agent Pipeline page) to generate an approval request.")

    st.divider()

    # ── Audit log ─────────────────────────────────────────────────────────────
    st.subheader("Audit Log")
    try:
        if not _AUDIT_DB.exists():
            raise FileNotFoundError
        with sqlite3.connect(_AUDIT_DB) as con:
            df_audit = pd.read_sql_query(
                "SELECT id, ts, agent, action, approved_by FROM audit ORDER BY id DESC LIMIT 10",
                con,
            )
        if df_audit.empty:
            st.info("No audit entries yet.")
        else:
            st.dataframe(df_audit, use_container_width=True, hide_index=True)
    except FileNotFoundError:
        st.info("No audit log yet — run a scenario first.")
    except Exception as exc:
        st.error(f"Could not read audit log: {exc}")

    st.divider()

    # ── Costs ─────────────────────────────────────────────────────────────────
    st.subheader("LLM Costs")
    try:
        if not _COSTS_DB.exists():
            raise FileNotFoundError
        with sqlite3.connect(_COSTS_DB) as con:
            df_costs = pd.read_sql_query(
                "SELECT agent, model, tokens_in, tokens_out, usd_estimate FROM costs ORDER BY id DESC LIMIT 50",
                con,
            )
        if df_costs.empty:
            st.info("No cost data yet.")
        else:
            total_usd = df_costs["usd_estimate"].sum()
            st.metric("Total Estimated Cost", f"${total_usd:.4f} USD")

            st.markdown("**Per-agent cost**")
            per_agent = (
                df_costs.groupby("agent")
                .agg({"tokens_in": "sum", "tokens_out": "sum", "usd_estimate": "sum"})
                .reset_index()
                .rename(columns={"usd_estimate": "USD estimate"})
            )
            st.dataframe(per_agent, use_container_width=True, hide_index=True)

            st.markdown("**Cost by model**")
            by_model = df_costs.groupby("model")["usd_estimate"].sum().reset_index()
            fig_pie = px.pie(
                by_model, values="usd_estimate", names="model",
                color_discrete_sequence=["#0F62FE", "#42be65", "#f1c21b", "#da1e28"],
            )
            fig_pie.update_layout(
                paper_bgcolor="#161616", font=dict(color="#f4f4f4"),
                height=280, margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    except FileNotFoundError:
        st.info("No cost data yet — run a scenario first.")
    except Exception as exc:
        st.error(f"Could not read cost data: {exc}")
