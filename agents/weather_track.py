"""WeatherTrackAgent — cyclone track and intensity analysis via Granite 4."""
from agents.base_agent import BaseAgent
from gateway import litellm_router

_SYSTEM = (
    "You are a tropical cyclone meteorologist. "
    "Analyse the provided cyclone data and produce a concise track and intensity summary "
    "covering current position, forecast path, wind speed, and storm surge risk. "
    "Be factual and brief."
)


class WeatherTrackAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="weather_track",
            model=litellm_router.GRANITE,
            system_prompt=_SYSTEM,
        )

    def run(self, cyclone_data: dict) -> str:
        user_msg = f"Cyclone data:\n{cyclone_data}"
        return self.call_llm(user_msg)
