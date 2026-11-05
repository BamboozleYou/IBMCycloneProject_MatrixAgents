"""Page 4 — Evacuation Plan & Human-in-the-Loop Approval."""
from __future__ import annotations
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.components.kpi_row import render_kpi_row

_AUDIT_DB = Path(__file__).parent.parent.parent / "audit.db"


def render() -> None:
    st.title("✅ Evacuation & Approval")

    results  = st.session_state.get("last_results")
    scenario = st.session_state.get("scenario", {})
    render_kpi_row(results, scenario)
    st.divider()

    st.subheader("Human-in-the-Loop Approval")

    if results and results.get("pending_approval"):
        evac_plan = results.get("evacuation_plan", "No plan text available.")
        shelter_result = results.get("shelter_result") or {}
        selected_shelters = shelter_result.get("selected", [])
        if selected_shelters:
            shelter_list = ", ".join(str(s) for s in selected_shelters)
        else:
            shelter_list = shelter_result.get("best_shelter", "—")
        cd        = results.get("cyclone_data", scenario)
        wj        = results.get("weather_json", {})

        # SMS preview
        imd_cls = wj.get("imd_class", f"Cat-{cd.get('category','?')}")
        sms_text = (
            f"⚠️ CYCLONE ALERT: {cd.get('name','CYCLONE')} ({imd_cls}) "
            f"approaching {cd.get('landfall','coast')}. "
            f"Evacuate NOW to: {shelter_list}. Follow official routes. "
            f"Wind {wj.get('peak_wind_kmh', cd.get('wind_kmh','?'))} km/h. "
            f"T-minus {wj.get('time_to_landfall_h','?')}h. Stay safe. #DisasterAlert"
        )
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
        st.info("Run a scenario first (Agent Pipeline page).")
render()
