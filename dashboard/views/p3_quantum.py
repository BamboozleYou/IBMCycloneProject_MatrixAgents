"""Page 3 — Quantum Optimiser: QAOA vs classical shelter selection."""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.components.kpi_row import render_kpi_row
from dashboard.components.theme import ACCENT, SURFACE, MUTED


def render() -> None:
    st.title("⚛ Quantum Optimiser — QAOA vs Classical")

    results  = st.session_state.get("last_results")
    scenario = st.session_state.get("scenario", {})
    render_kpi_row(results, scenario)
    st.divider()

    from mcp.qaoa_shelter import _load_shelters, _brute_force, build_qp, VILLAGE_ZONES, NUM_SELECT

    shelters  = _load_shelters()
    classical = _brute_force(shelters)

    try:
        from mcp.qaoa_shelter import _qaoa
        quantum     = _qaoa(shelters)
        qaoa_status = "✅ Ran on Qiskit Aer simulator"
    except Exception as exc:
        quantum = {
            "best_shelter":    classical["best_shelter"],
            "selected":        classical.get("selected", [classical["best_shelter"]]),
            "method":          "brute_force_fallback",
            "objective_value": classical["objective_value"],
            "sample_probs":    {},
            "capacity_ok":     classical["capacity_ok"],
        }
        qaoa_status = f"⚠️ Fallback ({exc.__class__.__name__}: {str(exc)[:60]})"

    match = set(quantum.get("selected", [])) == set(classical.get("selected", []))

    # ── Metrics ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("QAOA Selected",
              ", ".join(quantum.get("selected", [quantum["best_shelter"]])),
              f"obj = {quantum['objective_value']:.3f}")
    c2.metric("Classical Selected",
              ", ".join(classical.get("selected", [classical["best_shelter"]])),
              f"obj = {classical['objective_value']:.3f}")
    c3.metric("Agreement", "✅ Match" if match else "❌ Differs")
    c4.metric("QAOA Method", quantum["method"])
    c5.metric("Capacity OK", "✅ Yes" if quantum.get("capacity_ok") else "❌ No")
    st.caption(qaoa_status)
    st.divider()

    col_left, col_right = st.columns(2)

    # ── Per-shelter QP objective bar ──────────────────────────────────────────
    with col_left:
        st.subheader("QP Objective Score per Shelter")
        n = len(shelters)
        qp = build_qp(shelters)
        # single-shelter objective (feasibility aside)
        single_vals = []
        for i in range(n):
            x = [1.0 if j == i else 0.0 for j in range(n)]
            single_vals.append(qp.objective.evaluate(x))

        df_s = pd.DataFrame(shelters)
        df_s["qp_obj"] = single_vals
        selected_set = set(quantum.get("selected", [quantum["best_shelter"]]))
        colours = [ACCENT if row["name"] in selected_set else "#393939"
                   for _, row in df_s.iterrows()]

        fig_obj = go.Figure(go.Bar(
            x=df_s["name"], y=df_s["qp_obj"], marker_color=colours,
            hovertemplate="%{x}<br>QP obj: %{y:.3f}<extra></extra>",
        ))
        fig_obj.update_layout(
            paper_bgcolor=SURFACE, plot_bgcolor="#0a0a0a",
            font=dict(color="#f4f4f4"),
            xaxis=dict(tickangle=-25, color=MUTED),
            yaxis=dict(title="QP objective (lower=better)", color=MUTED),
            height=320, margin=dict(l=10, r=10, t=10, b=80),
        )
        st.plotly_chart(fig_obj, use_container_width=True)

    # ── Top-8 bitstring probability histogram ─────────────────────────────────
    with col_right:
        st.subheader("QAOA Top-8 Bitstring Distribution")
        sample_probs: dict[str, float] = quantum.get("sample_probs", {})

        if sample_probs:
            # already trimmed to top 8 in _qaoa; sort descending for display
            sorted_items = sorted(sample_probs.items(), key=lambda kv: kv[1], reverse=True)
            bitstrings = [k for k, _ in sorted_items]
            probs      = [v for _, v in sorted_items]
        else:
            # Derive top-8 from QP objective over all k-combinations
            from itertools import combinations as _comb
            combos = list(_comb(range(n), NUM_SELECT))
            raw_scores = []
            for c in combos:
                x = [1.0 if i in c else 0.0 for i in range(n)]
                raw_scores.append(1.0 / max(qp.objective.evaluate(x) + 1e-3, 1e-3))
            total_s = sum(raw_scores)
            all_bs = ["".join("1" if i in c else "0" for i in range(n)) for c in combos]
            all_probs = [s / total_s for s in raw_scores]
            # sort and keep top 8
            top8 = sorted(zip(all_bs, all_probs), key=lambda kv: kv[1], reverse=True)[:8]
            bitstrings = [k for k, _ in top8]
            probs = [v for _, v in top8]

        # Determine which bitstring corresponds to the QAOA-selected shelters
        selected_names_q = set(quantum.get("selected", [quantum["best_shelter"]]))
        def _bs_matches(bs: str) -> bool:
            return all(
                (bs[j] == "1") == (shelters[j]["name"] in selected_names_q)
                for j in range(n)
            )
        bar_colours = [ACCENT if _bs_matches(bs) else "#393939" for bs in bitstrings]

        fig_hist = go.Figure(go.Bar(
            x=bitstrings, y=probs,
            marker_color=bar_colours,
            hovertemplate="%{x}<br>P=%{y:.4f}<extra></extra>",
        ))
        fig_hist.update_layout(
            paper_bgcolor=SURFACE, plot_bgcolor="#0a0a0a",
            font=dict(color="#f4f4f4"),
            xaxis=dict(title="Bitstring (top 8)", color=MUTED, tickangle=-45),
            yaxis=dict(title="Probability", color=MUTED),
            height=320, margin=dict(l=10, r=10, t=10, b=80),
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # ── QAOA circuit ──────────────────────────────────────────────────────────
    st.subheader("QAOA Circuit (p=1)")
    try:
        from qiskit_algorithms import QAOA
        from qiskit_algorithms.optimizers import COBYLA
        from qiskit.primitives import Sampler
        from qiskit_optimization.converters import QuadraticProgramToQubo

        qubo = QuadraticProgramToQubo().convert(qp)
        sampler = Sampler()
        circuit = QAOA(sampler=sampler, optimizer=COBYLA(), reps=2).ansatz
        st.code(str(circuit.draw(output="text")), language="text")
    except Exception as exc:
        st.code(
            "q_0: ──H──Rz(γ)──Ry(β)──\n"
            + "\n".join(f"q_{i}: ──H──Rz(γ)──Ry(β)──" for i in range(1, n))
            + f"\n\n(p=1, {n} qubits — {exc.__class__.__name__})",
            language="text",
        )

    # ── Village zones map ─────────────────────────────────────────────────────
    st.subheader("Shelter Coverage Map")
    from mcp.qaoa_shelter import _haversine_km as _hav
    fig_cov = go.Figure()

    for z in VILLAGE_ZONES:
        fig_cov.add_trace(go.Scattermapbox(
            lat=[z["lat"]], lon=[z["lon"]], mode="markers+text",
            marker=dict(size=12, color="#f1c21b"),
            text=[z["name"]], textposition="top right",
            name=z["name"],
            hovertemplate=f"<b>{z['name']}</b><br>pop {z['pop']}<extra></extra>",
        ))

    for s in shelters:
        is_sel = s["name"] in selected_set
        fig_cov.add_trace(go.Scattermapbox(
            lat=[float(s["lat"])], lon=[float(s["lon"])], mode="markers+text",
            marker=dict(size=14 if is_sel else 9, color="#42be65" if is_sel else "#393939"),
            text=[s["name"]], textposition="top right",
            name=s["name"],
        ))

    fig_cov.update_layout(
        mapbox=dict(style="open-street-map", center=dict(lat=19.8, lon=85.7), zoom=7),
        margin=dict(l=0, r=0, t=0, b=0), height=420,
        paper_bgcolor=SURFACE,
        legend=dict(bgcolor=SURFACE, font=dict(color="#f4f4f4")),
    )
    st.plotly_chart(fig_cov, use_container_width=True)

    # ── Shelter candidates table ───────────────────────────────────────────────
    st.subheader("Shelter Candidates")
    df_disp = pd.DataFrame(shelters).rename(columns={
        "name": "Shelter", "capacity": "Capacity", "score": "Suitability Score",
        "lat": "Lat", "lon": "Lon",
    })
    df_disp["Avg dist to zones (km)"] = df_disp.apply(
        lambda row: round(
            sum(_hav(z["lat"], z["lon"], float(row["Lat"]), float(row["Lon"])) for z in VILLAGE_ZONES)
            / len(VILLAGE_ZONES), 1
        ), axis=1,
    )
    df_disp["Selected (QAOA)"] = df_disp["Shelter"].isin(selected_set)
    st.dataframe(df_disp, use_container_width=True, hide_index=True)


render()
