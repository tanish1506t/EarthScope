"""
Geospatial Map Visualization Module
Builds interactive global maps showing benchmark stations and user-selected targets.
"""

from typing import Dict, Any, Optional
import plotly.graph_objects as go

from earthscope.config import LOCATION_PRESETS, PARAMETERS_META
from earthscope.visualizations.theme import (
    COLOR_CYAN,
    COLOR_ROSE,
    COLOR_AMBER,
    COLOR_EMERALD,
    BG_COLOR,
    TEXT_COLOR,
    MUTED_TEXT,
    FONT_FAMILY
)


def create_global_earth_map(
    selected_lat: float,
    selected_lon: float,
    selected_name: str,
    active_var: str = "T2M",
    active_val: Optional[float] = None
) -> go.Figure:
    """
    Renders an interactive global map displaying benchmark observatories and the active analysis location.
    Uses Plotly Scattergeo for zero-token, highly reliable offline rendering with a dark space theme.
    """
    fig = go.Figure()

    # 1. Preset benchmark locations
    preset_lats = []
    preset_lons = []
    preset_texts = []
    preset_names = []

    for name, info in LOCATION_PRESETS.items():
        preset_lats.append(info["lat"])
        preset_lons.append(info["lon"])
        preset_names.append(name)
        text = (
            f"<b>{name}</b><br>"
            f"Region: {info.get('region', 'N/A')}<br>"
            f"Biome: {info.get('biome', 'N/A')}<br>"
            f"Coordinates: {info['lat']:.4f}°, {info['lon']:.4f}°<br>"
            f"<i>{info.get('significance', '')[:80]}...</i>"
        )
        preset_texts.append(text)

    # Trace: Benchmark stations
    fig.add_trace(go.Scattergeo(
        lon=preset_lons,
        lat=preset_lats,
        mode="markers",
        marker=dict(
            size=10,
            color=COLOR_CYAN,
            opacity=0.85,
            symbol="circle",
            line=dict(width=1.5, color="white")
        ),
        text=preset_texts,
        hoverinfo="text",
        name="Global Benchmark Observatories"
    ))

    # Trace: Active Selected Target (Pulsing ring effect)
    meta = PARAMETERS_META.get(active_var, {})
    units = meta.get("units", "")
    val_str = f"{active_val:.1f} {units}" if active_val is not None else "Analyzing..."

    target_text = (
        f"<b>🎯 ACTIVE TARGET: {selected_name}</b><br>"
        f"Latitude: {selected_lat:.4f}°<br>"
        f"Longitude: {selected_lon:.4f}°<br>"
        f"Current {meta.get('name', active_var)}: <b>{val_str}</b>"
    )

    # Outer glow
    fig.add_trace(go.Scattergeo(
        lon=[selected_lon],
        lat=[selected_lat],
        mode="markers",
        marker=dict(
            size=24,
            color="rgba(244, 63, 94, 0.3)",
            symbol="circle"
        ),
        hoverinfo="skip",
        showlegend=False
    ))

    # Inner core
    fig.add_trace(go.Scattergeo(
        lon=[selected_lon],
        lat=[selected_lat],
        mode="markers+text",
        marker=dict(
            size=14,
            color=COLOR_ROSE,
            symbol="diamond",
            line=dict(width=2, color="white")
        ),
        text=[f"  📍 {selected_name.split(',')[0]}"],
        textposition="top right",
        textfont=dict(family=FONT_FAMILY, size=12, color=COLOR_ROSE),
        hoverinfo="text",
        hovertext=[target_text],
        name="Active Investigation Site"
    ))

    # Dark celestial geo layout
    fig.update_geos(
        projection_type="natural earth",
        showland=True,
        landcolor="#0e1726",
        showocean=True,
        oceancolor="#050a14",
        showlakes=True,
        lakecolor="#050a14",
        showrivers=False,
        showcountries=True,
        countrycolor="#1e293b",
        countrywidth=0.8,
        showcoastlines=True,
        coastlinecolor="#334155",
        coastlinewidth=1.0,
        showframe=False,
        bgcolor=BG_COLOR
    )

    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        height=480,
        margin=dict(l=10, r=10, t=40, b=10),
        title=dict(
            text="<b>Geospatial Sensor Network & Investigation Target</b>",
            font=dict(family=FONT_FAMILY, size=15, color=TEXT_COLOR),
            x=0.02,
            y=0.96
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="right",
            x=0.98,
            font=dict(family=FONT_FAMILY, size=11, color=TEXT_COLOR),
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor="#334155",
            borderwidth=1
        )
    )

    return fig
