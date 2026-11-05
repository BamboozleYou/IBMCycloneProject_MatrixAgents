"""Supervisor — sequential agent orchestration with retries, guardrails, governance."""
from __future__ import annotations
import time
from pathlib import Path
from typing import Callable

import yaml

from agents.weather_track import WeatherTrackAgent, _wind_to_imd
from agents.impact import ImpactAgent
from agents.evacuation import EvacuationAgent
from guardrails.regex_guard import check_input, check_output, GuardError
from governance.audit import log_action
from memory.chroma_store import ChromaStore
from mcp.qaoa_shelter import optimise_shelters, DEMO_SHELTERS
from observability.logger import log_call

_POLICIES_PATH = Path(__file__).parent.parent / "governance" / "policies.yaml"
_MAX_RETRIES = 1  # gateway already falls back across 3 providers


def _load_policies() -> dict:
    return yaml.safe_load(_POLICIES_PATH.read_text()).get("agents", {})


class Supervisor:
    def __init__(self):
        self.policies = _load_policies()
        self.store = ChromaStore()
        self.store.seed()
        self.weather_agent   = WeatherTrackAgent()
        self.impact_agent    = ImpactAgent()
        self.evacuation_agent = EvacuationAgent()
        self.pending_approval = False

    # ------------------------------------------------------------------
    def _run_agent_with_retries(self, agent, input_text: str, extra_context: str = "") -> str:
        full_input = f"{extra_context}\n\n{input_text}".strip() if extra_context else input_text
        check_input(full_input)

        last_exc: Exception | None = None
        for attempt in range(1, _MAX_RETRIES + 2):  # 1 try + MAX_RETRIES retries
            t0 = time.monotonic()
            try:
                result = agent.call_llm(full_input)
                duration_ms = (time.monotonic() - t0) * 1000
                check_output(result)
                log_call(agent.name, agent.model, duration_ms, "ok", tokens=len(result.split()))
                log_action(agent.name, "llm_call", {"input": full_input[:200], "attempt": attempt})
                return result
            except GuardError:
                raise
            except Exception as exc:
                duration_ms = (time.monotonic() - t0) * 1000
                log_call(agent.name, agent.model, duration_ms, f"error:{exc}", tokens=0)
                last_exc = exc
                if attempt <= _MAX_RETRIES:
                    time.sleep(1.0)
        raise RuntimeError(f"Agent '{agent.name}' failed after {_MAX_RETRIES + 1} attempts: {last_exc}")

    # ------------------------------------------------------------------
    def run(self, cyclone_data: dict, on_step: Callable[[str, int], None] | None = None) -> dict:
        """Run the full pipeline sequentially. Returns result dict."""
        results: dict = {"cyclone_data": cyclone_data}

        # --- RAG context from ChromaDB ---
        query = str(cyclone_data.get("name", "")) + " cyclone storm surge evacuation"
        rag_docs = self.store.retrieve(query, k=2)
        rag_context = "Historical context:\n" + "\n".join(
            f"- {d['metadata'].get('name', d['id'])} ({d['metadata'].get('year', '')}): {d['summary'][:200]}"
            for d in rag_docs
        )

        # --- Step 1: WeatherTrack (returns JSON dict) ---
        wind_kmh = cyclone_data.get("wind_kmh", 0)
        weather_input = dict(cyclone_data)
        weather_input["imd_class"] = _wind_to_imd(wind_kmh)
        track_raw = self._run_agent_with_retries(
            self.weather_agent,
            input_text=str(weather_input),
            extra_context=rag_context,
        )
        # weather agent now returns a dict; supervisor stored raw str via call_llm path
        if isinstance(track_raw, dict):
            weather_json = track_raw
            track_summary = weather_json.get("summary", str(track_raw))
        else:
            from agents.weather_track import _parse_json
            weather_json = _parse_json(track_raw, cyclone_data)
            track_summary = weather_json.get("summary", track_raw)
        results["track_summary"] = track_summary
        results["weather_json"]  = weather_json
        if on_step:
            on_step("Weather", 25)

        # RAG: similar past cyclones
        rag_docs2 = self.store.retrieve(
            f"{weather_json.get('imd_class', '')} {cyclone_data.get('landfall', '')} cyclone", k=3
        )
        results["similar_cyclones"] = rag_docs2

        # --- Step 2: Impact ---
        impact_summary = self._run_agent_with_retries(
            self.impact_agent,
            input_text=track_summary,
            extra_context=rag_context,
        )
        results["impact_summary"] = impact_summary
        if on_step:
            on_step("Impact", 50)

        # --- Step 3: QAOA shelter optimisation ---
        shelter_result = optimise_shelters(DEMO_SHELTERS)
        results["shelter_result"] = shelter_result
        if on_step:
            on_step("QAOA", 70)

        # --- Step 4: Evacuation ---
        evac_policy = self.policies.get("evacuation", {})
        selected_shelters = shelter_result.get("selected", [shelter_result["best_shelter"]])
        evac_plan = self._run_agent_with_retries(
            self.evacuation_agent,
            input_text=impact_summary,
            extra_context=(
                f"{rag_context}\n\n"
                f"Optimal shelter (QAOA): {shelter_result['best_shelter']} "
                f"[method={shelter_result['method']}, obj={shelter_result['objective_value']}]\n"
                f"All selected shelters: {selected_shelters}"
            ),
        )
        results["evacuation_plan"] = evac_plan
        if on_step:
            on_step("Evacuation", 95)

        # Set HITL flag from policy
        self.pending_approval = bool(evac_policy.get("require_human_approval", True))
        results["pending_approval"] = self.pending_approval

        log_action("supervisor", "pipeline_complete", {"cyclone": cyclone_data.get("name", "unknown")})
        return results
