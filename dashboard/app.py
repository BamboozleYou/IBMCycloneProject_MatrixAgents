"""CycloneShield-Q · Streamlit dashboard — Prototype demo data."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Paths ──────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent
_AUDIT_DB = _ROOT / "audit.db"

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CycloneShield-Q",
    page_icon="🌀",
    layout="wide",
)

st.sidebar.title("🌀 CycloneShield-Q")
st.sidebar.caption("Prototype demo data")
page = st.sidebar.radio(
    "Navigate",
    ["Run Scenario & Agent Activity", "Quantum Optimiser", "Approval & Logs"],
)

# ══════════════════════════════════════════════════════════════════════════
# PAGE 1 — Run Scenario + Agent Activity
# ══════════════════════════════════════════════════════════════════════════
if page == "Run Scenario & Agent Activity":
    st.title("Run Scenario & Agent Activity")
    st.caption("Prototype demo data")

    # --- Scenario input ---
    with st.expander("Configure cyclone scenario", expanded=True):
        col1, col2, col3 = st.columns(3)
        name     = col1.text_input("Cyclone name",  value="Demo-Alpha")
        category = col2.selectbox("Category", [1, 2, 3, 4, 5], index=2)
        landfall = col3.text_input("Landfall location", value="Odisha Coast")
        wind_kmh = col1.number_input("Max wind (km/h)", value=180, step=10)
        radius   = col2.number_input("Radius (km)", value=120, step=10)
        pop_risk = col3.number_input("Population at risk (k)", value=450, step=50)

    run_btn = st.button("▶ Run Scenario", type="primary")

    # --- Agent status table (prototype) ---
    st.subheader("Agent Activity")

    if run_btn:
        cyclone_data = {
            "name": name, "category": category, "landfall": landfall,
            "wind_kmh": wind_kmh, "radius_km": radius, "pop_at_risk_k": pop_risk,
        }
        # Simulate sequential agent execution with live status updates
        agents_cfg = [
            ("WeatherTrack",  "weather_track", "Tracks trajectory & intensity"),
            ("Impact",        "impact",        "Estimates damage & affected zones"),
            ("QAOA Optimiser","qaoa_shelter",  "Selects optimal evacuation shelter"),
            ("Evacuation",    "evacuation",    "Generates evacuation plan"),
        ]

        status_placeholder = st.empty()

        rows = [{"Agent": a, "Role": r, "Status": "⏳ Queued", "Output": ""} for a, _, r in agents_cfg]
        df_status = pd.DataFrame(rows)
        status_placeholder.dataframe(df_status, use_container_width=True, hide_index=True)

        progress = st.progress(0)

        try:
            import sys
            sys.path.insert(0, str(_ROOT))
            from agents.supervisor import Supervisor

            sup = Supervisor()

            # Patch to capture per-step results progressively
            step_results: list[tuple[str, str]] = []

            orig_run = sup._run_agent_with_retries.__func__  # noqa: SLF001 — monkey-patch

            def _patched(self_inner, agent, input_text, extra_context=""):
                result = orig_run(self_inner, agent, input_text, extra_context)
                step_results.append((agent.name, result))
                return result

            import types
            sup._run_agent_with_retries = types.MethodType(_patched, sup)

            results = sup.run(cyclone_data)
            st.session_state["last_results"] = results

            # Build final status table
            status_map = {n: r for n, r in step_results}
            final_rows = []
            for disp, key, role in agents_cfg:
                agent_key = key.replace("_", "") if key != "qaoa_shelter" else "qaoa_shelter"
                if key == "qaoa_shelter":
                    sr = results.get("shelter_result", {})
                    final_rows.append({
                        "Agent": disp, "Role": role,
                        "Status": "✅ Done",
                        "Output": f"{sr.get('best_shelter','')} [{sr.get('method','')}]",
                    })
                else:
                    # match by agent name substring
                    matched = next(
                        (v for k, v in status_map.items() if key.split("_")[0].lower() in k.lower()),
                        "—",
                    )
                    final_rows.append({
                        "Agent": disp, "Role": role,
                        "Status": "✅ Done",
                        "Output": (matched[:120] + "…") if len(matched) > 120 else matched,
                    })

            progress.progress(100)
            status_placeholder.dataframe(
                pd.DataFrame(final_rows), use_container_width=True, hide_index=True
            )
            st.success("Pipeline complete. See **Approval & Logs** to approve the evacuation plan.")

        except Exception as exc:
            st.error(f"Pipeline error: {exc}")
            st.info("Showing prototype demo output below.")
            progress.progress(100)
            demo_rows = [
                {"Agent": "WeatherTrack",   "Role": "Tracks trajectory & intensity",      "Status": "⚠️ Demo",  "Output": "Cat-3 landfall Odisha in ~18 h, 180 km/h winds [demo]"},
                {"Agent": "Impact",          "Role": "Estimates damage & affected zones",  "Status": "⚠️ Demo",  "Output": "~450 k people at risk, storm surge 3–5 m [demo]"},
                {"Agent": "QAOA Optimiser",  "Role": "Selects optimal evacuation shelter", "Status": "⚠️ Demo",  "Output": "Sports Arena E [brute_force, obj=900.0] [demo]"},
                {"Agent": "Evacuation",      "Role": "Generates evacuation plan",          "Status": "⚠️ Demo",  "Output": "Zones A-D: immediate evacuation via NH-16 [demo]"},
            ]
            status_placeholder.dataframe(
                pd.DataFrame(demo_rows), use_container_width=True, hide_index=True
            )
    else:
        # Static demo table until Run is pressed
        demo_idle = pd.DataFrame([
            {"Agent": "WeatherTrack",   "Status": "Idle", "Role": "Tracks trajectory & intensity"},
            {"Agent": "Impact",          "Status": "Idle", "Role": "Estimates damage & affected zones"},
            {"Agent": "QAOA Optimiser",  "Status": "Idle", "Role": "Selects optimal evacuation shelter"},
            {"Agent": "Evacuation",      "Status": "Idle", "Role": "Generates evacuation plan"},
        ])
        st.dataframe(demo_idle, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════
# PAGE 2 — Quantum Optimiser
# ══════════════════════════════════════════════════════════════════════════
elif page == "Quantum Optimiser":
    st.title("Quantum Optimiser — QAOA vs Classical")
    st.caption("Prototype demo data")

    import sys
    sys.path.insert(0, str(_ROOT))
    from mcp.qaoa_shelter import DEMO_SHELTERS, _brute_force

    shelters = DEMO_SHELTERS

    # Classical results (always available)
    classical = _brute_force(shelters)

    # QAOA attempt
    try:
        from mcp.qaoa_shelter import _qaoa
        quantum = _qaoa(shelters)
        qaoa_status = "✅ Ran on Qiskit Aer simulator"
    except Exception as exc:
        quantum = {"best_shelter": classical["best_shelter"], "method": "qaoa_fallback", "objective_value": classical["objective_value"]}
        qaoa_status = f"⚠️ Fallback to brute-force ({exc.__class__.__name__})"

    # Comparison table
    st.subheader("Shelter candidates")
    df_shelters = pd.DataFrame(shelters)
    df_shelters["score_capacity"] = df_shelters["capacity"] * df_shelters["score"]
    st.dataframe(df_shelters.rename(columns={"name": "Shelter", "capacity": "Capacity", "score": "Suitability Score", "score_capacity": "Objective (cap×score)"}),
                 use_container_width=True, hide_index=True)

    st.subheader("Optimisation results")
    st.info(f"QAOA status: {qaoa_status}")

    result_rows = [
        {"Method": "🔵 Classical (brute-force)", "Best Shelter": classical["best_shelter"],
         "Objective Value": classical["objective_value"], "Agreement": "—"},
        {"Method": "🟣 Quantum (QAOA)",           "Best Shelter": quantum["best_shelter"],
         "Objective Value": quantum["objective_value"],
         "Agreement": "✅ Match" if quantum["best_shelter"] == classical["best_shelter"] else "❌ Differs"},
    ]
    st.dataframe(pd.DataFrame(result_rows), use_container_width=True, hide_index=True)

    col_q, col_c = st.columns(2)
    col_q.metric("QAOA — Best Shelter",      quantum["best_shelter"],   f"obj = {quantum['objective_value']:.0f}")
    col_c.metric("Classical — Best Shelter", classical["best_shelter"], f"obj = {classical['objective_value']:.0f}")

    # Bar chart of objective values
    st.subheader("Objective value per shelter")
    chart_df = pd.DataFrame({
        "Shelter": [s["name"] for s in shelters],
        "Objective (cap × score)": [s["capacity"] * s["score"] for s in shelters],
    }).set_index("Shelter")
    st.bar_chart(chart_df)

# ══════════════════════════════════════════════════════════════════════════
# PAGE 3 — Approval & Logs
# ══════════════════════════════════════════════════════════════════════════
elif page == "Approval & Logs":
    st.title("Approval & Logs")
    st.caption("Prototype demo data")

    import sys
    sys.path.insert(0, str(_ROOT))

    # --- Pending approval ---
    st.subheader("Human-in-the-Loop Approval")
    results = st.session_state.get("last_results")

    if results and results.get("pending_approval"):
        evac_plan = results.get("evacuation_plan", "No plan text available.")
        st.warning("⏳ Evacuation plan is pending human approval.")
        with st.expander("Evacuation plan", expanded=True):
            st.write(evac_plan)

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
            st.success(f"Plan approved by **{approver}** and logged to audit.")

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
        st.info("Run a scenario first (page 1) to generate an approval request. Showing demo audit log below.")

    st.divider()

    # --- Audit log ---
    st.subheader("Audit Log")
    try:
        if not _AUDIT_DB.exists():
            raise FileNotFoundError("audit.db not found")
        with sqlite3.connect(_AUDIT_DB) as con:
            df_audit = pd.read_sql_query(
                "SELECT id, ts, agent, action, approved_by, payload_hash FROM audit ORDER BY id DESC LIMIT 50",
                con,
            )
        if df_audit.empty:
            raise ValueError("empty")
        st.dataframe(df_audit, use_container_width=True, hide_index=True)
    except Exception:
        # Demo fallback
        demo_audit = pd.DataFrame([
            {"id": 5, "ts": "2026-11-04T16:00:05Z", "agent": "supervisor",    "action": "evacuation_approved", "approved_by": "operator-1", "payload_hash": "ab12…"},
            {"id": 4, "ts": "2026-11-04T16:00:04Z", "agent": "supervisor",    "action": "pipeline_complete",   "approved_by": None,          "payload_hash": "cd34…"},
            {"id": 3, "ts": "2026-11-04T16:00:03Z", "agent": "evacuation",    "action": "llm_call",            "approved_by": None,          "payload_hash": "ef56…"},
            {"id": 2, "ts": "2026-11-04T16:00:02Z", "agent": "impact",        "action": "llm_call",            "approved_by": None,          "payload_hash": "gh78…"},
            {"id": 1, "ts": "2026-11-04T16:00:01Z", "agent": "weather_track", "action": "llm_call",            "approved_by": None,          "payload_hash": "ij90…"},
        ])
        st.dataframe(demo_audit, use_container_width=True, hide_index=True)

    st.divider()

    # --- Token costs ---
    st.subheader("Token Costs")
    # Attempt to read costs.db if present, else use demo data
    _COSTS_DB = _ROOT / "costs.db"
    try:
        if not _COSTS_DB.exists():
            raise FileNotFoundError
        with sqlite3.connect(_COSTS_DB) as con:
            df_costs = pd.read_sql_query("SELECT * FROM costs ORDER BY id DESC LIMIT 50", con)
        if df_costs.empty:
            raise ValueError("empty")
        st.dataframe(df_costs, use_container_width=True, hide_index=True)
    except Exception:
        demo_costs = pd.DataFrame([
            {"Agent": "weather_track", "Model": "watsonx/granite-3.0-8b-instruct", "Tokens": 312,  "Est. Cost (USD)": 0.0006},
            {"Agent": "impact",        "Model": "watsonx/granite-3.0-8b-instruct", "Tokens": 428,  "Est. Cost (USD)": 0.0009},
            {"Agent": "evacuation",    "Model": "watsonx/granite-3.0-8b-instruct", "Tokens": 540,  "Est. Cost (USD)": 0.0011},
            {"Agent": "TOTAL",         "Model": "—",                               "Tokens": 1280, "Est. Cost (USD)": 0.0026},
        ])
        st.dataframe(demo_costs, use_container_width=True, hide_index=True)
        st.caption("Demo token data. Connect costs.db to see live figures.")
