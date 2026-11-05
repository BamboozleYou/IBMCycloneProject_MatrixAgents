"""ImpactAgent — impact zone and population risk assessment via Gemini."""
from agents.base_agent import BaseAgent
from gateway import litellm_router

_SYSTEM = (
    "You are a disaster-impact analyst. "
    "Given a cyclone track summary, identify the most affected districts, "
    "estimate population at risk, critical infrastructure exposure, and flood/wind damage zones. "
    "Output a structured impact assessment."
)


class ImpactAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="impact",
            model=litellm_router.GEMINI,
            system_prompt=_SYSTEM,
        )

    def run(self, track_summary: str) -> str:
        return self.call_llm(f"Track summary:\n{track_summary}")
