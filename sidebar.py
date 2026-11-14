"""
Sidebar Controls and Navigation Component
Provides location selection (presets & custom coordinates), temporal window filters,
variable selection, and multi-page routing.
"""

from typing import Dict, Any, Tuple
import streamlit as st

from earthscope.config import (
    LOCATION_PRESETS,
    DEFAULT_LOCATION_KEY,
    PARAMETERS_META,
    DEFAULT_START_YEAR,
    DEFAULT_END_YEAR,
    MIN_YEAR,
    MAX_YEAR
)


def render_sidebar() -> Dict[str, Any]:
    """
    Renders sidebar controls and returns state dictionary.
    """
    with st.sidebar:
        st.html("""
        <div style="text-align: center; padding: 12px 0 16px 0;">
            <div style="font-size: 28px; margin-bottom: 4px;">🛰️</div>
            <div style="font-size: 18px; font-weight: 800; color: #00f0ff; letter-spacing: -0.02em;">EARTHSCOPE</div>
            <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em;">Earth Trend Explorer</div>
        </div>
        """)

        st.markdown("---")

        # Page Navigation
        page_options = [
            "🏠 Overview Dashboard",
            "🌡️ Temperature Explorer",
            "🌧️ Precipitation Explorer",
            "🌿 Vegetation & Land Trends",
            "🌍 Planetary Climate (NASA GISTEMP)",
            "🗺️ Interactive Global Map",
            "🔬 Trend Analysis Lab",
            "🤖 AI Scientific Insights",
            "📚 Data Sources & Methodology",
            "👥 About CodeRex"
        ]

        selected_page = st.radio(
            "Investigation Modules",
            options=page_options,
            index=0,
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### 📍 Location Target")

        location_mode = st.radio(
            "Selection Mode",
            ["Preset Observatory", "Custom Coordinates"],
            horizontal=True
        )

        preset_keys = list(LOCATION_PRESETS.keys())
        default_preset_idx = preset_keys.index(DEFAULT_LOCATION_KEY) if DEFAULT_LOCATION_KEY in preset_keys else 0

        if location_mode == "Preset Observatory":
            chosen_preset = st.selectbox(
                "Benchmark Observatories",
                options=preset_keys,
                index=default_preset_idx
            )
            preset_data = LOCATION_PRESETS[chosen_preset]
            lat = float(preset_data["lat"])
            lon = float(preset_data["lon"])
            location_label = chosen_preset
            biome_info = preset_data.get("biome", "")
        else:
            col_lat, col_lon = st.columns(2)
            with col_lat:
                lat = st.number_input("Latitude (°)", min_value=-90.0, max_value=90.0, value=19.9975, step=0.01, format="%.4f")
            with col_lon:
                lon = st.number_input("Longitude (°)", min_value=-180.0, max_value=180.0, value=73.7898, step=0.01, format="%.4f")
            custom_name = st.text_input("Location Name", value=f"Point ({lat:.2f}°, {lon:.2f}°)")
            location_label = custom_name
            biome_info = "Custom Coordinate Point"

        st.markdown("---")
        st.markdown("### 📅 Temporal Horizon")

        col_y1, col_y2 = st.columns(2)
        with col_y1:
            start_year = st.number_input("Start Year", min_value=MIN_YEAR, max_value=MAX_YEAR, value=DEFAULT_START_YEAR, step=1)
        with col_y2:
            end_year = st.number_input("End Year", min_value=MIN_YEAR, max_value=MAX_YEAR, value=DEFAULT_END_YEAR, step=1)

        if start_year > end_year:
            st.error("Start Year cannot exceed End Year.")
            start_year = end_year

        # Aggregation Selection
        agg_mode = st.selectbox(
            "Temporal Aggregation",
            options=["Daily", "Monthly", "Annual"],
            index=0
        )

        st.markdown("---")
        st.markdown("### ⚙️ NASA POWER Query")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            refresh_btn = st.button("🔄 Sync NASA", width="stretch", type="primary")
        with col_btn2:
            clear_cache_btn = st.button("🧹 Clear Cache", width="stretch")

        st.html("""
        <div style="font-size: 11px; color: #64748b; margin-top: 16px; padding: 10px; background: rgba(15,23,42,0.6); border-radius: 8px; border: 1px solid #1e293b;">
            <strong>NASA POWER API v2</strong><br>
            Community: Agroclimatology (AG)<br>
            Fill Value: -999.0 masked to NaN<br>
            Team CodeRex • 2026
        </div>
        """)

        return {
            "page": selected_page,
            "location_name": location_label,
            "lat": lat,
            "lon": lon,
            "biome": biome_info,
            "start_year": int(start_year),
            "end_year": int(end_year),
            "aggregation": agg_mode,
            "refresh_triggered": refresh_btn,
            "clear_cache_triggered": clear_cache_btn
        }
