"""QAOA shelter optimiser — picks best shelter via Qiskit QAOA or brute-force fallback.

Returns: {"best_shelter": str, "method": str, "objective_value": float}
"""
from __future__ import annotations
import json
from typing import Any


# ---------------------------------------------------------------------------
# Brute-force
# ---------------------------------------------------------------------------

def _brute_force(shelters: list[dict]) -> dict:
    """Select the single shelter with maximum capacity * score."""
    best = max(shelters, key=lambda s: s["capacity"] * s["score"])
    return {
        "best_shelter":    best["name"],
        "method":          "brute_force",
        "objective_value": float(best["capacity"] * best["score"]),
    }


# ---------------------------------------------------------------------------
# QAOA (Qiskit Aer)
# ---------------------------------------------------------------------------

def _qaoa(shelters: list[dict]) -> dict:
    from qiskit_algorithms import QAOA
    from qiskit_algorithms.optimizers import COBYLA
    from qiskit.primitives import Sampler
    from qiskit_optimization import QuadraticProgram
    from qiskit_optimization.algorithms import MinimumEigenOptimizer

    n = len(shelters)
    qp = QuadraticProgram(name="shelter_select")
    for i, s in enumerate(shelters):
        qp.binary_var(name=f"x{i}")

    # Maximise sum(capacity*score*x_i) → minimise negative
    linear = {f"x{i}": -s["capacity"] * s["score"] for i, s in enumerate(shelters)}
    qp.minimize(linear=linear)

    # Exactly-one constraint
    qp.linear_constraint(
        linear={f"x{i}": 1 for i in range(n)},
        sense="==",
        rhs=1,
        name="pick_one",
    )

    sampler = Sampler()
    qaoa = QAOA(sampler=sampler, optimizer=COBYLA(), reps=1)
    optimizer = MinimumEigenOptimizer(qaoa)
    result = optimizer.solve(qp)

    chosen_idx = next(i for i, v in enumerate(result.x) if v > 0.5)
    best = shelters[chosen_idx]
    return {
        "best_shelter":    best["name"],
        "method":          "qaoa",
        "objective_value": float(best["capacity"] * best["score"]),
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def optimise_shelters(shelters: list[dict]) -> dict:
    """
    shelters: list of {"name": str, "capacity": int, "score": float}
    Returns best shelter selection dict.
    """
    if len(shelters) > 8:
        return _brute_force(shelters)
    try:
        return _qaoa(shelters)
    except Exception:
        return _brute_force(shelters)


# ---------------------------------------------------------------------------
# Demo 5-shelter fixture (used when run directly)
# ---------------------------------------------------------------------------

DEMO_SHELTERS = [
    {"name": "Community Hall A",  "capacity": 500, "score": 0.85},
    {"name": "School Block B",    "capacity": 300, "score": 0.90},
    {"name": "Railway Station C", "capacity": 800, "score": 0.70},
    {"name": "Temple Complex D",  "capacity": 250, "score": 0.95},
    {"name": "Sports Arena E",    "capacity": 1200, "score": 0.75},
]


if __name__ == "__main__":
    result = optimise_shelters(DEMO_SHELTERS)
    print(json.dumps(result, indent=2))
