"""
Interactive Global Map Page for EarthScope
"""

from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd

from earthscope.config import LOCATION_PRESETS, PARAMETERS_META
from earthscope.visualizations.maps import create_global_earth_map
from earthscope.components.cards import render_metric_card_html, render_alert_callout


def render_map_page(
    df: pd.DataFrame,
    location_name: str,
    lat: float,
    lon: float,
    biome: str,
    start_year: int,
    end_year: int
) -> None:
    """
    Renders the Interactive Global Map page.
    """
    st.markdown("### 🗺️ Planetary Geospatial Observatory & Target Locator")

    # Current variable value preview
    active_val = None
    if not df.empty and "T2M" in df.columns:
        active_val = float(df["T2M"].dropna().iloc[-1]) if not df["T2M"].dropna().empty else None

    # Global Map
    fig_map = create_global_earth_map(
        selected_lat=lat,
        selected_lon=lon,
        selected_name=location_name,
        active_var="T2M",
        active_val=active_val
    )
    st.plotly_chart(fig_map)

    st.markdown("---")

    # Details Grid
    c_info, c_presets = st.columns([1.2, 1.8])

    with c_info:
        st.markdown("#### 🎯 Active Investigation Site")
        st.html(f"""
        <div style="background: #0f172a; border: 1px solid #334155; border-radius: 12px; padding: 18px; font-size: 13px; color: #cbd5e1; line-height: 1.6;">
            <div style="font-size: 18px; font-weight: 700; color: #00f0ff; margin-bottom: 6px;">
                {location_name}
            </div>
            <div style="font-size: 12px; color: #94a3b8; margin-bottom: 12px;">
                <strong>Latitude:</strong> {lat:.4f}° | <strong>Longitude:</strong> {lon:.4f}°<br>
                <strong>Ecosystem / Biome:</strong> {biome}
            </div>
            <div style="border-top: 1px solid #1e293b; padding-top: 10px; margin-top: 10px; font-size: 12px; color: #cbd5e1;">
                <strong>Spatial Grid Resolution:</strong><br>
                Atmosphere & Solar: 0.5° × 0.5° (approx. 50 km × 50 km)<br>
                Land Surface: 0.625° × 0.5° (~62 km × 50 km)
            </div>
        </div>
        """)

        callout = render_alert_callout(
            "<strong>Spatial Representation Note:</strong> In NASA POWER point queries, data represents the area-weighted spatial average of the corresponding MERRA-2 assimilation grid cell containing the coordinates, rather than a single pinpoint thermometer probe.",
            level="info"
        )
        st.html(callout)

    with c_presets:
        st.markdown("#### 🌐 Global Benchmark Observatories Catalog")
        st.caption("Select any preset observatory in the sidebar to pivot the investigation across global biomes.")

        preset_rows = []
        for name, data in LOCATION_PRESETS.items():
            preset_rows.append({
                "Station / Region": name.split(",")[0],
                "Biome": data.get("biome", "N/A"),
                "Lat (°)": f"{data['lat']:.2f}",
                "Lon (°)": f"{data['lon']:.2f}",
                "Significance": data.get("significance", "")[:70] + "..."
            })

        st.dataframe(pd.DataFrame(preset_rows), hide_index=True)
