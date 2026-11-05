"""Page 5 — Audit Log & LLM Costs."""
from __future__ import annotations
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.components.kpi_row import render_kpi_row
from dashboard.components.theme import SURFACE

_AUDIT_DB = Path(__file__).parent.parent.parent / "audit.db"
_COSTS_DB = Path(__file__).parent.parent.parent / "costs.db"


def render() -> None:
    st.title("📋 Audit & Costs")

    results  = st.session_state.get("last_results")
    scenario = st.session_state.get("scenario", {})
    render_kpi_row(results, scenario)
    st.divider()

    # ── Audit log ─────────────────────────────────────────────────────────────
    st.subheader("Audit Log")
    try:
        if not _AUDIT_DB.exists():
            raise FileNotFoundError
        with sqlite3.connect(_AUDIT_DB) as con:
            df_audit = pd.read_sql_query(
                "SELECT id, ts, agent, action, approved_by FROM audit ORDER BY id DESC LIMIT 20",
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
            st.metric("Total Estimated Cost", f"${df_costs['usd_estimate'].sum():.4f} USD")

            st.markdown("**Per-agent cost**")
            per_agent = (
                df_costs.groupby("agent")
                .agg({"tokens_in": "sum", "tokens_out": "sum", "usd_estimate": "sum"})
                .reset_index()
                .rename(columns={"usd_estimate": "USD estimate"})
            )
            st.dataframe(per_agent, use_container_width=True, hide_index=True)

            by_model = df_costs.groupby("model")["usd_estimate"].sum().reset_index()
            fig_pie = px.pie(by_model, values="usd_estimate", names="model",
                             color_discrete_sequence=["#0F62FE", "#42be65", "#f1c21b", "#da1e28"])
            fig_pie.update_layout(paper_bgcolor=SURFACE, font=dict(color="#f4f4f4"),
                                  height=280, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig_pie, use_container_width=True)
    except FileNotFoundError:
        st.info("No cost data yet — run a scenario first.")
    except Exception as exc:
        st.error(f"Could not read cost data: {exc}")
