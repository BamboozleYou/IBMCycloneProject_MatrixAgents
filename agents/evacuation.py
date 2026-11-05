"""EvacuationAgent — shelter routing and evacuation orders via Groq."""
from agents.base_agent import BaseAgent
from gateway import litellm_router

_SYSTEM = (
    "You are an emergency evacuation coordinator. "
    "Given an impact assessment and the recommended optimal shelter from the QAOA optimiser, "
    "produce a prioritised evacuation plan: affected zones, shelter assignments, "
    "route recommendations, and a public advisory message."
)


class EvacuationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="evacuation",
            model=litellm_router.GROQ,
            system_prompt=_SYSTEM,
        )

    def run(self, impact_summary: str, shelter_result: dict | None = None) -> str:
        context = f"Impact assessment:\n{impact_summary}"
        if shelter_result:
            context += (
                f"\n\nOptimal shelter (QAOA result):\n"
                f"  Name: {shelter_result.get('best_shelter', 'N/A')}\n"
                f"  Method: {shelter_result.get('method', 'N/A')}\n"
                f"  Objective value: {shelter_result.get('objective_value', 'N/A')}"
            )
        return self.call_llm(context)
