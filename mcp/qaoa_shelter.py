"""QAOA shelter optimiser — choose 2–3 shelters from data/shelters.csv to cover
5 village zones within capacity, minimising total travel distance.

Returns:
    {
        "best_shelter": str,          # name of top-ranked selected shelter
        "selected":     list[str],    # all chosen shelter names
        "method":       str,
        "objective_value": float,
        "sample_probs": dict[str, float],  # bitstring → probability from QAOA
        "capacity_ok":  bool,
    }
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
_CSV = Path(__file__).parent.parent / "data" / "shelters.csv"

# Five village zones (lat, lon, population)
VILLAGE_ZONES = [
    {"name": "Zone-N", "lat": 20.2, "lon": 85.5, "pop": 4000},
    {"name": "Zone-NE","lat": 20.1, "lon": 86.0, "pop": 3500},
    {"name": "Zone-E", "lat": 19.8, "lon": 86.2, "pop": 5000},
    {"name": "Zone-S", "lat": 19.4, "lon": 85.8, "pop": 2800},
    {"name": "Zone-W", "lat": 19.6, "lon": 85.2, "pop": 3200},
]

NUM_SELECT = 2   # choose this many shelters (2–3)


def _load_shelters() -> list[dict]:
    """Load shelters from CSV, fall back to DEMO_SHELTERS if file missing."""
    if _CSV.exists():
        df = pd.read_csv(_CSV)
        return df.to_dict(orient="records")
    return DEMO_SHELTERS


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _objective(selected_shelters: list[dict]) -> float:
    """
    Minimise: total (zone_pop × min_distance_to_selected_shelter).
    Lower is better.
    """
    total = 0.0
    for zone in VILLAGE_ZONES:
        dists = [
            _haversine_km(zone["lat"], zone["lon"], s["lat"], s["lon"])
            for s in selected_shelters
        ]
        total += zone["pop"] * min(dists)
    return total


def _capacity_ok(selected_shelters: list[dict]) -> bool:
    """Total capacity of chosen shelters must cover total zone population."""
    total_pop = sum(z["pop"] for z in VILLAGE_ZONES)
    total_cap = sum(int(s["capacity"]) for s in selected_shelters)
    return total_cap >= total_pop


# ---------------------------------------------------------------------------
# Shared QuadraticProgram builder
# ---------------------------------------------------------------------------

def build_qp(shelters: list[dict]):
    """Build the QuadraticProgram used by both QAOA and brute-force evaluation.

    Objective (minimise):
      Linear  : x_i = d_i / max(d) − 1.5 × capacity_i / tot
                where d_i = sum(zone_pop × dist(zone, shelter_i)) / tot
                and   tot = total zone population
      Quadratic: for each pair i < j,
                  0.5 × max(0, 1 − dist_km(i,j) / 40)

    Constraint: exactly NUM_SELECT shelters selected.
    """
    from qiskit_optimization import QuadraticProgram

    n = len(shelters)
    tot = sum(z["pop"] for z in VILLAGE_ZONES)

    qp = QuadraticProgram(name="shelter_cover")

    for i in range(n):
        qp.binary_var(name=f"x{i}")

    # --- linear coefficients ---
    d_vals: list[float] = []
    for s in shelters:
        d_i = sum(
            z["pop"] * _haversine_km(z["lat"], z["lon"], float(s["lat"]), float(s["lon"]))
            for z in VILLAGE_ZONES
        ) / tot
        d_vals.append(d_i)

    max_d = max(d_vals) if d_vals else 1.0

    linear: dict[str, float] = {}
    for i, s in enumerate(shelters):
        linear[f"x{i}"] = d_vals[i] / max_d - 1.5 * float(s["capacity"]) / tot

    # --- quadratic coefficients (overlap penalty) ---
    quadratic: dict[tuple[str, str], float] = {}
    for i in range(n):
        for j in range(i + 1, n):
            dist_ij = _haversine_km(
                float(shelters[i]["lat"]), float(shelters[i]["lon"]),
                float(shelters[j]["lat"]), float(shelters[j]["lon"]),
            )
            penalty = 0.5 * max(0.0, 1.0 - dist_ij / 40.0)
            if penalty > 0:
                quadratic[(f"x{i}", f"x{j}")] = penalty

    qp.minimize(linear=linear, quadratic=quadratic)

    # Constraint: select exactly NUM_SELECT
    qp.linear_constraint(
        linear={f"x{i}": 1 for i in range(n)},
        sense="==",
        rhs=NUM_SELECT,
        name="pick_k",
    )

    return qp


# ---------------------------------------------------------------------------
# Brute-force (exhaustive over all C(n,k) combinations)
# ---------------------------------------------------------------------------

def _brute_force(shelters: list[dict]) -> dict:
    """Exhaustively evaluate build_qp objective for every combination of NUM_SELECT."""
    from itertools import combinations

    n = len(shelters)
    qp = build_qp(shelters)

    best_idx: list[int] | None = None
    best_val = float("inf")

    for combo in combinations(range(n), NUM_SELECT):
        x = [1.0 if i in combo else 0.0 for i in range(n)]
        val = qp.objective.evaluate(x)
        if val < best_val:
            best_val = val
            best_idx = list(combo)

    selected_shelters = [shelters[i] for i in (best_idx or [])]
    selected_names = [s["name"] for s in selected_shelters]

    return {
        "best_shelter":    selected_names[0] if selected_names else "—",
        "selected":        selected_names,
        "method":          "brute_force",
        "objective_value": float(best_val),
        "sample_probs":    {},
        "capacity_ok":     _capacity_ok(selected_shelters),
    }


# ---------------------------------------------------------------------------
# QAOA (Qiskit Aer)
# ---------------------------------------------------------------------------

def _qaoa(shelters: list[dict]) -> dict:
    from qiskit_algorithms import QAOA
    from qiskit_algorithms.optimizers import COBYLA
    from qiskit.primitives import Sampler
    from qiskit_optimization.algorithms import MinimumEigenOptimizer
    from qiskit_algorithms.utils import algorithm_globals

    algorithm_globals.random_seed = 7

    n = len(shelters)
    qp = build_qp(shelters)

    sampler = Sampler(options={"seed": 7})
    qaoa = QAOA(sampler=sampler, optimizer=COBYLA(maxiter=200), reps=2)
    optimizer = MinimumEigenOptimizer(qaoa)
    result = optimizer.solve(qp)

    # Extract sample probabilities: convert Qiskit little-endian integer keys
    # to bitstrings with format(k, f'0{n}b')[::-1]
    sample_probs: dict[str, float] = {}
    try:
        raw = result.min_eigen_solver_result
        if hasattr(raw, "samples"):
            for s in raw.samples:
                bs = "".join(str(int(b)) for b in s.x)
                sample_probs[bs] = float(s.probability)
        elif hasattr(raw, "eigenstate") and hasattr(raw.eigenstate, "items"):
            for k, v in raw.eigenstate.items():
                p = float(v)
                if p > 1e-6:
                    bs = format(k, f"0{n}b")[::-1]
                    sample_probs[bs] = p
    except Exception:
        pass

    # Keep only the top 8 by probability
    sample_probs = dict(
        sorted(sample_probs.items(), key=lambda kv: kv[1], reverse=True)[:8]
    )

    selected_indices = [i for i, v in enumerate(result.x) if v > 0.5]
    selected_shelters = [shelters[i] for i in selected_indices]
    selected_names = [s["name"] for s in selected_shelters]

    obj_val = qp.objective.evaluate(
        [1.0 if i in selected_indices else 0.0 for i in range(n)]
    ) if selected_indices else float(result.fval)

    return {
        "best_shelter":    selected_names[0] if selected_names else "—",
        "selected":        selected_names,
        "method":          "qaoa",
        "objective_value": float(obj_val),
        "sample_probs":    sample_probs,
        "capacity_ok":     _capacity_ok(selected_shelters),
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def optimise_shelters(shelters: list[dict] | None = None) -> dict:
    """
    shelters: list of {"name", "lat", "lon", "capacity", "score"}.
    If None, loads from data/shelters.csv.
    """
    if shelters is None:
        shelters = _load_shelters()
    if len(shelters) > 12:
        return _brute_force(shelters)
    try:
        return _qaoa(shelters)
    except Exception:
        return _brute_force(shelters)


# ---------------------------------------------------------------------------
# Demo fixture (kept for backward-compatibility with dashboard imports)
# ---------------------------------------------------------------------------

DEMO_SHELTERS = [
    {"name": "Community Hall A",  "lat": 19.9, "lon": 85.6, "capacity": 5000,  "score": 0.85},
    {"name": "School Block B",    "lat": 19.7, "lon": 85.9, "capacity": 3000,  "score": 0.90},
    {"name": "Railway Station C", "lat": 20.1, "lon": 86.1, "capacity": 8000,  "score": 0.70},
    {"name": "Temple Complex D",  "lat": 19.5, "lon": 85.4, "capacity": 2500,  "score": 0.95},
    {"name": "Sports Arena E",    "lat": 20.3, "lon": 85.7, "capacity": 12000, "score": 0.75},
]


if __name__ == "__main__":
    result = optimise_shelters()
    print(json.dumps(result, indent=2))
