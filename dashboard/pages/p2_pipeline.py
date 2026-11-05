"""Page 2 — Agent Pipeline: run supervisor, per-agent status cards."""
from __future__ import annotations
import sqlite3
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.components.kpi_row import render_kpi_row

_COSTS_DB = Path(__file__).parent.parent.parent / "costs.db"

_AGENTS_META = [
    ("Weather",    "weather_track",  "weather_json",    "Granite"),
    ("Impact",     "impact",         "impact_summary",  "Gemini"),
    ("QAOA",       "qaoa_shelter",   "shelter_result",  "Qiskit"),
    ("Evacuation", "evacuation",     "evacuation_plan", "Groq"),
    ("Approval",   "hitl",           "pending_approval","Human"),
]


def render() -> None:
    st.title("🤖 Agent Pipeline")

    results  = st.session_state.get("last_results")
    scenario = st.session_state.get("scenario", {})
    render_kpi_row(results, scenario)
    st.divider()

    # ── Flow diagram ──────────────────────────────────────────────────────────
    done_keys = set(results.keys()) if results else set()

    def _node_bg(res_key: str) -> str:
        if results is None:
            return "#393939"
        return "#42be65" if res_key in done_keys else "#393939"

    flow_html = '<div style="display:flex;align-items:center;flex-wrap:wrap;gap:6px;margin:10px 0 20px 0;">'
    for i, (label, _, res_key, _model) in enumerate(_AGENTS_META):
        bg = _node_bg(res_key)
        flow_html += f'<span style="display:inline-block;padding:6px 14px;border-radius:20px;font-size:13px;font-weight:600;margin:0 4px;background:{bg};color:#f4f4f4;">{label}</span>'
        if i < len(_AGENTS_META) - 1:
            flow_html += '<span style="color:#8d8d8d;font-size:18px;">→</span>'
    flow_html += "</div>"
    st.markdown(flow_html, unsafe_allow_html=True)

    # ── Run button ────────────────────────────────────────────────────────────
    scenario_data = st.session_state.get("scenario") or {
        "name": "Demo-Alpha", "landfall": "Odisha Coast",
        "wind_kmh": 185, "radius_km": 130, "pop_at_risk_k": 450,
        "lat0": 19.5, "lon0": 87.5, "lat_land": 19.8, "lon_land": 85.8,
    }

    if st.button("▶ Run Pipeline", type="primary"):
        progress = st.progress(0, "Initialising…")
        step_results: dict = {}
        try:
            from agents.supervisor import Supervisor
            import types

            sup = Supervisor()
            orig = sup._run_agent_with_retries.__func__  # noqa: SLF001

            def _patched(self_inner, agent, input_text, extra_context=""):
                t0 = time.monotonic()
                res = orig(self_inner, agent, input_text, extra_context)
                step_results[agent.name] = (agent.model, res, time.monotonic() - t0)
                return res

            sup._run_agent_with_retries = types.MethodType(_patched, sup)
            progress.progress(10, "Running agents…")
            run_results = sup.run(scenario_data)
            st.session_state["last_results"] = run_results
            st.session_state["step_results"] = step_results
            progress.progress(100, "Pipeline complete ✅")
            st.success("Pipeline complete — see Approval & Logs.")
        except Exception as exc:
            st.error(f"Pipeline error: {exc}")
            progress.progress(100)

    # ── Agent cards ───────────────────────────────────────────────────────────
    results     = st.session_state.get("last_results")
    step_results = st.session_state.get("step_results", {})

    cost_map: dict = {}
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
        return

    output_map = {
        "weather_track": str(results.get("weather_json", results.get("track_summary", ""))),
        "impact":        results.get("impact_summary", ""),
        "qaoa_shelter":  str(results.get("shelter_result", "")),
        "evacuation":    results.get("evacuation_plan", ""),
    }

    for label, key, res_key, model_hint in _AGENTS_META[:-1]:
        content = output_map.get(key, "")
        sr = step_results.get(key, (model_hint, content, 0.0))
        elapsed = sr[2]
        cm = cost_map.get(key, {})

        with st.expander(f"**{label}** · {sr[0] or model_hint}", expanded=bool(content)):
            mcol1, mcol2, mcol3 = st.columns(3)
            mcol1.metric("Tokens in",  cm.get("tokens_in",  "—"))
            mcol2.metric("Tokens out", cm.get("tokens_out", "—"))
            mcol3.metric("Time", f"{elapsed:.1f}s" if elapsed else "—")
            st.markdown(content or "_No output_")

    # Weather JSON details
    wj = results.get("weather_json")
    if wj:
        st.divider()
        st.subheader("Weather Agent JSON Output")
        import json
        st.json(wj)
