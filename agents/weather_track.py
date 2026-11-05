"""WeatherTrackAgent — returns structured JSON + narrative summary."""
from __future__ import annotations
import json
import math
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
Use the provided lat/lon/wind data directly. Do not invent numbers.
Use only the numbers provided. Do not add dates, death tolls or population figures."""


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


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _parse_json(raw: str, fallback: dict) -> dict:
    """Extract JSON from LLM output; fall back to computed values if parsing fails."""
    # Strip markdown fences if present
    text = re.sub(r"```[a-z]*\n?", "", raw).strip()
    data: dict | None = None
    try:
        parsed = json.loads(text)
        required = {"landfall_lat", "landfall_lon", "time_to_landfall_h", "imd_class", "confidence"}
        if required.issubset(parsed.keys()):
            data = parsed
    except (json.JSONDecodeError, ValueError):
        pass

    if data is None:
        # Fallback: derive from input data
        wind = float(fallback.get("wind_kmh", 120))
        data = {
            "landfall_lat":       float(fallback.get("lat_land", fallback.get("lat0", 19.8))),
            "landfall_lon":       float(fallback.get("lon_land", fallback.get("lon0", 85.8))),
            "time_to_landfall_h": None,
            "imd_class":          _wind_to_imd(wind),
            "confidence":         0.75,
            "peak_wind_kmh":      wind,
            "storm_surge_m":      None,
            "summary":            raw[:400],
        }

    # (a) always override imd_class from peak_wind_kmh
    peak_wind = float(data.get("peak_wind_kmh") or fallback.get("wind_kmh", 120))
    data["imd_class"] = _wind_to_imd(peak_wind)

    # (b) always compute time_to_landfall_h from distance
    lat0 = float(fallback.get("lat0", data.get("landfall_lat", 19.8)))
    lon0 = float(fallback.get("lon0", data.get("landfall_lon", 85.8)))
    lat_land = float(data.get("landfall_lat", lat0))
    lon_land = float(data.get("landfall_lon", lon0))
    dist_km = _haversine_km(lat0, lon0, lat_land, lon_land)
    data["time_to_landfall_h"] = round(dist_km / 15.0, 1)

    # (c) compute storm_surge_m if missing
    if data.get("storm_surge_m") is None:
        data["storm_surge_m"] = round(peak_wind / 60.0, 1)

    # (d) join summary list into markdown bullets
    if isinstance(data.get("summary"), list):
        data["summary"] = "\n".join(f"- {item}" for item in data["summary"])

    # (e) clamp confidence to 0–1
    if data.get("confidence") is not None:
        data["confidence"] = max(0.0, min(1.0, float(data["confidence"])))

    return data


def _wind_to_imd(wind_kmh: float) -> str:
    if wind_kmh <= 63:  return "Depression"
    if wind_kmh <= 89:  return "Deep Depression"
    if wind_kmh <= 117: return "Cyclonic Storm"
    if wind_kmh <= 166: return "Severe Cyclonic Storm"
    if wind_kmh <= 221: return "Very Severe Cyclonic Storm"
    if wind_kmh <= 260: return "Extremely Severe Cyclonic Storm"
    return "Super Cyclonic Storm"
