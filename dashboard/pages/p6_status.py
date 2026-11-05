"""Page 6 — System Status: provider health, ChromaDB stats, observability."""
from __future__ import annotations
import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.components.kpi_row import render_kpi_row

_CHROMA_DB = Path(__file__).parent.parent.parent / "chroma_db"


def _key_status(env: str) -> tuple[bool, str]:
    v = os.environ.get(env, "")
    ok = bool(v) and not v.startswith("your_")
    return ok, ("🟢 Connected" if ok else "🔴 Not configured")


def render() -> None:
    st.title("⚙️ System Status")

    results  = st.session_state.get("last_results")
    scenario = st.session_state.get("scenario", {})
    render_kpi_row(results, scenario)
    st.divider()

    # ── LLM providers ─────────────────────────────────────────────────────────
    st.subheader("LLM Providers")
    providers = [
        ("Granite 4 (watsonx)", "WATSONX_API_KEY"),
        ("Gemini Flash",        "GEMINI_API_KEY"),
        ("Groq LLaMA-3.1",     "GROQ_API_KEY"),
    ]
    cols = st.columns(len(providers))
    for col, (name, env) in zip(cols, providers):
        ok, status = _key_status(env)
        col.metric(name, status, delta_color="normal" if ok else "inverse")

    st.divider()

    # ── ChromaDB stats ────────────────────────────────────────────────────────
    st.subheader("ChromaDB Vector Store")
    try:
        from memory.chroma_store import ChromaStore
        store = ChromaStore()
        store.seed()
        count = store._col.count()
        st.metric("Seeded documents", count)

        # Show all stored cyclones
        all_docs = store._col.get(include=["metadatas", "documents"])
        rows = []
        for i, doc_id in enumerate(all_docs["ids"]):
            meta = all_docs["metadatas"][i]
            rows.append({
                "ID":      doc_id,
                "Name":    meta.get("name", ""),
                "Year":    meta.get("year", ""),
                "Category": meta.get("category", ""),
                "Region":  meta.get("landfall_region", ""),
            })
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    except Exception as exc:
        st.error(f"ChromaDB error: {exc}")

    st.divider()

    # ── Observability log tail ─────────────────────────────────────────────────
    st.subheader("Recent Observability Logs")
    log_dir = Path(__file__).parent.parent.parent / "logs"
    try:
        log_files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not log_files:
            raise FileNotFoundError
        log_path = log_files[0]
        lines = log_path.read_text().splitlines()[-30:]
        st.code("\n".join(lines), language="text")
        st.caption(f"File: {log_path.name}")
    except FileNotFoundError:
        st.info("No log files found yet.")
    except Exception as exc:
        st.error(f"Log read error: {exc}")

    st.divider()

    # ── Session state inspector ────────────────────────────────────────────────
    st.subheader("Session State Keys")
    keys = list(st.session_state.keys())
    if keys:
        st.code(str(keys), language="python")
    else:
        st.info("Session state is empty.")
