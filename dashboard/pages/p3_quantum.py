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

    from mcp.qaoa_shelter import _load_shelters, _brute_force, _objective, VILLAGE_ZONES, NUM_SELECT

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
        }
        qaoa_status = f"⚠️ Fallback ({exc.__class__.__name__}: {str(exc)[:60]})"

    match = set(quantum.get("selected", [])) == set(classical.get("selected", []))

    # ── Metrics ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("QAOA Selected",
              ", ".join(quantum.get("selected", [quantum["best_shelter"]])),
              f"obj = {quantum['objective_value']:.0f}")
    c2.metric("Classical Selected",
              ", ".join(classical.get("selected", [classical["best_shelter"]])),
              f"obj = {classical['objective_value']:.0f}")
    c3.metric("Agreement", "✅ Match" if match else "❌ Differs")
    c4.metric("QAOA Method", quantum["method"])
    st.caption(qaoa_status)
    st.divider()

    col_left, col_right = st.columns(2)

    # ── Per-shelter distance-score bar ────────────────────────────────────────
    with col_left:
        st.subheader("Distance Score per Shelter")
        df_s = pd.DataFrame(shelters)
        df_s["obj"] = df_s.apply(lambda r: _objective([r.to_dict()]), axis=1)
        selected_set = set(quantum.get("selected", [quantum["best_shelter"]]))
        colours = [ACCENT if n in selected_set else "#393939" for n in df_s["name"]]

        fig_obj = go.Figure(go.Bar(
            x=df_s["name"], y=df_s["obj"], marker_color=colours,
            hovertemplate="%{x}<br>pop×km: %{y:.0f}<extra></extra>",
        ))
        fig_obj.update_layout(
            paper_bgcolor=SURFACE, plot_bgcolor="#0a0a0a",
            font=dict(color="#f4f4f4"),
            xaxis=dict(tickangle=-25, color=MUTED),
            yaxis=dict(title="pop × km (lower=better)", color=MUTED),
            height=320, margin=dict(l=10, r=10, t=10, b=80),
        )
        st.plotly_chart(fig_obj, use_container_width=True)

    # ── Bitstring probability histogram ───────────────────────────────────────
    with col_right:
        st.subheader("QAOA Bitstring Distribution")
        sample_probs: dict[str, float] = quantum.get("sample_probs", {})

        if sample_probs:
            bitstrings = list(sample_probs.keys())
            probs      = list(sample_probs.values())
        else:
            # Objective-weighted distribution over all valid k-combinations
            from itertools import combinations as _comb
            n = len(shelters)
            combos = list(_comb(range(n), NUM_SELECT))
            raw_scores = [1.0 / max(_objective([shelters[i] for i in c]), 1e-3) for c in combos]
            total_s = sum(raw_scores)
            bitstrings = ["".join("1" if i in c else "0" for i in range(n)) for c in combos]
            probs = [s / total_s for s in raw_scores]

        selected_names_q = set(quantum.get("selected", [quantum["best_shelter"]]))
        selected_bs_idx = {
            i for i, bs in enumerate(bitstrings)
            if all((bs[j] == "1") == (shelters[j]["name"] in selected_names_q)
                   for j in range(len(shelters)))
        }
        bar_colours = [ACCENT if i in selected_bs_idx else "#393939"
                       for i in range(len(bitstrings))]

        fig_hist = go.Figure(go.Bar(
            x=bitstrings, y=probs,
            marker_color=bar_colours,
            hovertemplate="%{x}<br>P=%{y:.4f}<extra></extra>",
        ))
        fig_hist.update_layout(
            paper_bgcolor=SURFACE, plot_bgcolor="#0a0a0a",
            font=dict(color="#f4f4f4"),
            xaxis=dict(title="Bitstring", color=MUTED, tickangle=-45),
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
        from qiskit_optimization import QuadraticProgram
        from qiskit_optimization.converters import QuadraticProgramToQubo
        from mcp.qaoa_shelter import _haversine_km

        n = len(shelters)
        qp = QuadraticProgram(name="shelter_cover")
        for i in range(n):
            qp.binary_var(name=f"x{i}")
        avg_pop = sum(z["pop"] for z in VILLAGE_ZONES) / len(VILLAGE_ZONES)
        linear_c = {
            f"x{i}": sum(_haversine_km(z["lat"], z["lon"], float(s["lat"]), float(s["lon"]))
                         for z in VILLAGE_ZONES) / len(VILLAGE_ZONES) * avg_pop
            for i, s in enumerate(shelters)
        }
        qp.minimize(linear=linear_c)
        qp.linear_constraint(linear={f"x{i}": 1 for i in range(n)}, sense="==",
                              rhs=NUM_SELECT, name="pick_k")
        qubo = QuadraticProgramToQubo().convert(qp)
        sampler = Sampler()
        circuit = QAOA(sampler=sampler, optimizer=COBYLA(), reps=1).ansatz
        st.code(str(circuit.draw(output="text")), language="text")
    except Exception as exc:
        n = len(shelters)
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
