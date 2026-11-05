"""WeatherTrackAgent — returns structured JSON + narrative summary."""
from __future__ import annotations
import json
import re

from agents.base_agent import BaseAgent
from gateway import litellm_router

_SYSTEM = """You are a tropical cyclone meteorologist for the Indian coast.
Given cyclone input data, respond with ONLY valid JSON (no markdown fences) in this exact schema:
{
  "landfall_lat": <float>,
  "landfall_lon": <float>,
  "time_to_landfall_h": <float>,
  "imd_class": "<one of: Depression|Deep Depression|Cyclonic Storm|Severe Cyclonic Storm|Very Severe Cyclonic Storm|Extremely Severe Cyclonic Storm|Super Cyclonic Storm>",
  "confidence": <float 0-1>,
  "peak_wind_kmh": <float>,
  "storm_surge_m": <float>,
  "summary": "<3-5 bullet-point narrative, max 120 words>"
}
Use the provided lat/lon/wind data directly. Do not invent numbers."""


class WeatherTrackAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="weather_track",
            model=litellm_router.GRANITE,
            system_prompt=_SYSTEM,
            max_tokens=512,
        )

    def run(self, cyclone_data: dict) -> dict:  # type: ignore[override]
        user_msg = f"Cyclone data (use these values directly):\n{json.dumps(cyclone_data, indent=2)}"
        raw = self.call_llm(user_msg)
        return _parse_json(raw, cyclone_data)


def _parse_json(raw: str, fallback: dict) -> dict:
    """Extract JSON from LLM output; fall back to computed values if parsing fails."""
    # Strip markdown fences if present
    text = re.sub(r"```[a-z]*\n?", "", raw).strip()
    try:
        data = json.loads(text)
        # Validate required keys
        required = {"landfall_lat", "landfall_lon", "time_to_landfall_h", "imd_class", "confidence"}
        if required.issubset(data.keys()):
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: derive from input data
    wind = float(fallback.get("wind_kmh", 120))
    imd = _wind_to_imd(wind)
    return {
        "landfall_lat":       float(fallback.get("lat_land", fallback.get("lat0", 19.8))),
        "landfall_lon":       float(fallback.get("lon_land", fallback.get("lon0", 85.8))),
        "time_to_landfall_h": 24.0,
        "imd_class":          imd,
        "confidence":         0.75,
        "peak_wind_kmh":      wind,
        "storm_surge_m":      round(wind / 100, 1),
        "summary":            raw[:400],
    }


def _wind_to_imd(wind_kmh: float) -> str:
    if wind_kmh <= 63:  return "Depression"
    if wind_kmh <= 89:  return "Deep Depression"
    if wind_kmh <= 117: return "Cyclonic Storm"
    if wind_kmh <= 166: return "Severe Cyclonic Storm"
    if wind_kmh <= 221: return "Very Severe Cyclonic Storm"
    if wind_kmh <= 260: return "Extremely Severe Cyclonic Storm"
    return "Super Cyclonic Storm"
