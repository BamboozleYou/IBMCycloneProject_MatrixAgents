"""Map builder — draws cyclone track from weather_json + shelter markers."""
from __future__ import annotations
import math

import numpy as np
import plotly.graph_objects as go

from dashboard.components.theme import ACCENT, GREEN, RED, ORANGE, MUTED, SURFACE


def build_track_map(
    scenario: dict,
    weather_json: dict | None = None,
    chosen_shelters: list[str] | None = None,
) -> go.Figure:
    """
    Build a Scattermapbox figure from scenario + weather_json.
    weather_json keys used: landfall_lat, landfall_lon.
    Falls back to scenario lat0/lon0/lat_land/lon_land if missing.
    """
    wj = weather_json or {}
    lat_land = float(wj.get("landfall_lat") or scenario.get("lat_land", 19.8))
    lon_land = float(wj.get("landfall_lon") or scenario.get("lon_land", 85.8))
    lat0     = float(scenario.get("lat0", lat_land - 0.5))
    lon0     = float(scenario.get("lon0", lon_land + 1.5))
    wind_kmh = float(wj.get("peak_wind_kmh") or scenario.get("wind_kmh", 150))
    radius   = float(scenario.get("radius_km", 100))

    n_steps = 12
    lats = np.linspace(lat0, lat_land, n_steps)
    lons = np.linspace(lon0, lon_land, n_steps)

    fig = go.Figure()

    # Cone of uncertainty
    cone_lons_hi = [lon + radius / 222 for lon in lons]
    cone_lons_lo = [lon - radius / 222 for lon in lons]
    cone_lats = list(lats) + list(lats[::-1]) + [lats[0]]
    cone_lons = cone_lons_hi + cone_lons_lo[::-1] + [cone_lons_hi[0]]
    fig.add_trace(go.Scattermapbox(
        lat=cone_lats, lon=cone_lons, fill="toself",
        fillcolor="rgba(15,98,254,0.12)", line=dict(width=0),
        name="Uncertainty cone", hoverinfo="skip",
    ))

    # Forecast track
    fig.add_trace(go.Scattermapbox(
        lat=list(lats), lon=list(lons), mode="lines",
        line=dict(color=ACCENT, width=2), opacity=0.5,
        name="Forecast track",
        hovertemplate="Lat %{lat:.2f} Lon %{lon:.2f}<extra></extra>",
    ))

    # Current position (most recent = lat0)
    fig.add_trace(go.Scattermapbox(
        lat=[lat0], lon=[lon0], mode="markers",
        marker=dict(size=18, color=ORANGE, symbol="circle"),
        name="Current position",
        hovertemplate=f"<b>{scenario.get('name','Cyclone')}</b><br>Wind {wind_kmh:.0f} km/h<extra></extra>",
    ))

    # Landfall marker (from weather_json)
    conf = wj.get("confidence")
    lf_label = f"Landfall ({wj.get('imd_class','')}, conf={conf:.0%})" if conf else "Landfall"
    fig.add_trace(go.Scattermapbox(
        lat=[lat_land], lon=[lon_land], mode="markers+text",
        marker=dict(size=16, color=RED, symbol="star"),
        text=[lf_label], textposition="top right",
        name="Landfall",
        hovertemplate=f"<b>Landfall</b><br>{scenario.get('landfall','')}<extra></extra>",
    ))

    # Impact radius circle
    angles = list(range(0, 361, 5))
    r_deg = radius / 111.0
    circle_lats = [lat_land + r_deg * math.sin(a * math.pi / 180) for a in angles]
    circle_lons = [lon_land + r_deg * math.cos(a * math.pi / 180) for a in angles]
    fig.add_trace(go.Scattermapbox(
        lat=circle_lats, lon=circle_lons, mode="lines",
        line=dict(color=ORANGE, width=1), opacity=0.6,
        name=f"Impact radius ({radius:.0f} km)", hoverinfo="skip",
    ))

    # Shelters from CSV
    try:
        import pandas as pd
        from pathlib import Path
        _CSV = Path(__file__).parent.parent.parent / "data" / "shelters.csv"
        if _CSV.exists():
            df = pd.read_csv(_CSV)
            chosen_set = set(chosen_shelters or [])
            for _, row in df.iterrows():
                is_chosen = row["name"] in chosen_set
                fig.add_trace(go.Scattermapbox(
                    lat=[float(row["lat"])], lon=[float(row["lon"])],
                    mode="markers+text",
                    marker=dict(size=14 if is_chosen else 9,
                                color=GREEN if is_chosen else MUTED),
                    text=[row["name"]], textposition="top right",
                    name=row["name"],
                    hovertemplate=(
                        f"<b>{row['name']}</b><br>"
                        f"Cap {int(row['capacity'])} · Score {row['score']}"
                        "<extra></extra>"
                    ),
                ))
    except Exception:
        pass

    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=(lat0 + lat_land) / 2, lon=(lon0 + lon_land) / 2),
            zoom=5,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=520,
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        legend=dict(bgcolor=SURFACE, font=dict(color="#f4f4f4"), x=0, y=1),
        showlegend=True,
    )
    return fig
