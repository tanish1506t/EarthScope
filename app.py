"""
EarthScope — Earth System Trend Detective
NASA Space Apps Challenge 2026 | Team CodeRex
Main Streamlit Application Entrypoint
"""

import os
import sys
from datetime import datetime, date
import streamlit as st
import pandas as pd

# Ensure earthscope package is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from earthscope.config import (
    APP_NAME,
    APP_SUBTITLE,
    TEAM_NAME,
    DEFAULT_LOCATION_KEY,
    DEFAULT_START_YEAR,
    DEFAULT_END_YEAR,
    PARAMETERS_META
)
from earthscope.data.nasa_power_client import NASAPowerClient, NASADataRetrievalError
from earthscope.data.data_cleaning import parse_and_clean_nasa_data
from earthscope.data.aggregation import aggregate_monthly, aggregate_annual
from earthscope.components.sidebar import render_sidebar
from earthscope.components.header import render_header_html
from earthscope.components.report_generator import generate_markdown_report, generate_html_report

# Page implementations
from earthscope.pages.page_overview import render_overview_page
from earthscope.pages.page_temperature import render_temperature_page
from earthscope.pages.page_precipitation import render_precipitation_page
from earthscope.pages.page_vegetation import render_vegetation_page
from earthscope.pages.page_map import render_map_page
from earthscope.pages.page_trend_lab import render_trend_lab_page
from earthscope.pages.page_ai_insights import render_ai_insights_page
from earthscope.pages.page_methodology import render_methodology_page
from earthscope.pages.page_about import render_about_page
from earthscope.pages.page_gistemp import render_gistemp_page

# Configure Streamlit page
st.set_page_config(
    page_title=f"{APP_NAME} — {APP_SUBTITLE}",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Space Dark Theme CSS
CUSTOM_CSS = """
<style>
    /* Global Background & Typography */
    .stApp {
        background-color: #081226;
        color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Top decoration bar */
    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0b0f19;
        border-right: 1px solid #1e293b;
    }

    /* Clean Card Containers */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border-color: #1e293b !important;
    }

    /* Custom Scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #081226;
    }
    ::-webkit-scrollbar-thumb {
        background: #1e293b;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #00f0ff;
    }

    /* Streamlit Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        border-color: #00f0ff;
        box-shadow: 0 0 12px rgba(0, 240, 255, 0.25);
        color: #00f0ff;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00f0ff 0%, #0284c7 100%);
        color: #081226;
        border: none;
        font-weight: 700;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 0 16px rgba(0, 240, 255, 0.4);
        color: #081226;
    }

    /* Metric Containers */
    div[data-testid="stMetricValue"] {
        color: #f8fafc;
        font-weight: 700;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_resource
def get_nasa_client() -> NASAPowerClient:
    """Returns singleton NASA POWER API client with disk caching."""
    return NASAPowerClient(cache_enabled=True)


def load_data_pipeline(
    lat: float,
    lon: float,
    start_year: int,
    end_year: int,
    force_refresh: bool = False
):
    """
    Executes full data ingestion and preparation pipeline:
    API Call -> Cleaning & Validation -> Monthly & Annual Aggregation.
    """
    client = get_nasa_client()
    start_date = f"{start_year}0101"
    # Bound end date to current available period
    current_year = datetime.now().year
    if end_year >= current_year:
        end_date = f"{end_year}1231"
    else:
        end_date = f"{end_year}1231"

    requested_parameters = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN", "TS", "GWETROOT", "RH2M", "WS2M"]

    try:
        raw_payload = client.fetch_daily_data(
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date,
            parameters=requested_parameters,
            force_refresh=force_refresh
        )

        daily_df, quality_report = parse_and_clean_nasa_data(raw_payload)
        monthly_df = aggregate_monthly(daily_df)
        annual_df = aggregate_annual(monthly_df)

        retrieval_meta = raw_payload.get("_retrieval_metadata", {})
        retrieval_meta["mode"] = raw_payload.get("_retrieval_mode", "live")

        return daily_df, monthly_df, annual_df, quality_report, retrieval_meta, None

    except Exception as err:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}, {}, str(err)


def main():
    # Render Sidebar Controls
    controls = render_sidebar()

    # Clear cache trigger
    if controls.get("clear_cache_triggered"):
        client = get_nasa_client()
        removed = client.clear_cache()
        st.sidebar.success(f"Cache cleared: {removed} records removed.")

    # Data Pipeline Execution
    with st.spinner(f"🛰️ Ingesting NASA observations for {controls['location_name']}..."):
        daily_df, monthly_df, annual_df, quality_report, ret_meta, error_msg = load_data_pipeline(
            lat=controls["lat"],
            lon=controls["lon"],
            start_year=controls["start_year"],
            end_year=controls["end_year"],
            force_refresh=controls.get("refresh_triggered", False)
        )

    # Header Banner
    sync_time = ret_meta.get("retrieved_at", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
    mode_tag = " [Cache]" if ret_meta.get("mode") == "cached" else " [Live API]"
    api_status_label = f"Connected to NASA POWER v2{mode_tag}" if not error_msg else "API Disconnected"

    st.html(render_header_html(
        location_name=controls["location_name"],
        lat=controls["lat"],
        lon=controls["lon"],
        api_status=api_status_label,
        last_retrieval=sync_time
    ))

    # Error handling state
    if error_msg:
        st.error(f"""
        ### ⚠️ NASA Data Retrieval Notice
        **Failed to retrieve observations from NASA POWER:** {error_msg}
        
        **Troubleshooting:**
        1. Check internet connectivity.
        2. Ensure coordinates are within valid bounds (Lat: -90 to +90, Lon: -180 to +180).
        3. Click **'🔄 Sync NASA'** in the sidebar to retry the request.
        """)
        return

    # Multi-page Routing
    page = controls["page"]

    if page == "🏠 Overview Dashboard":
        render_overview_page(
            df=daily_df,
            monthly_df=monthly_df,
            annual_df=annual_df,
            quality_report=quality_report,
            location_name=controls["location_name"],
            lat=controls["lat"],
            lon=controls["lon"],
            biome=controls["biome"],
            start_year=controls["start_year"],
            end_year=controls["end_year"],
            retrieval_meta=ret_meta
        )

    elif page == "🌡️ Temperature Explorer":
        render_temperature_page(
            df=daily_df,
            monthly_df=monthly_df,
            annual_df=annual_df,
            location_name=controls["location_name"],
            lat=controls["lat"],
            lon=controls["lon"],
            start_year=controls["start_year"],
            end_year=controls["end_year"]
        )

    elif page == "🌧️ Precipitation Explorer":
        render_precipitation_page(
            df=daily_df,
            monthly_df=monthly_df,
            annual_df=annual_df,
            location_name=controls["location_name"],
            lat=controls["lat"],
            lon=controls["lon"],
            start_year=controls["start_year"],
            end_year=controls["end_year"]
        )

    elif page == "🌿 Vegetation & Land Trends":
        render_vegetation_page(
            df=daily_df,
            monthly_df=monthly_df,
            annual_df=annual_df,
            location_name=controls["location_name"],
            lat=controls["lat"],
            lon=controls["lon"],
            start_year=controls["start_year"],
            end_year=controls["end_year"]
        )

    elif page == "🌍 Planetary Climate (NASA GISTEMP)":
        render_gistemp_page(
            local_annual_df=annual_df,
            location_name=controls["location_name"]
        )

    elif page == "🗺️ Interactive Global Map":
        render_map_page(
            df=daily_df,
            location_name=controls["location_name"],
            lat=controls["lat"],
            lon=controls["lon"],
            biome=controls["biome"],
            start_year=controls["start_year"],
            end_year=controls["end_year"]
        )

    elif page == "🔬 Trend Analysis Lab":
        render_trend_lab_page(
            df=daily_df,
            monthly_df=monthly_df,
            annual_df=annual_df,
            location_name=controls["location_name"],
            lat=controls["lat"],
            lon=controls["lon"],
            start_year=controls["start_year"],
            end_year=controls["end_year"]
        )

    elif page == "🤖 AI Scientific Insights":
        render_ai_insights_page(
            df=daily_df,
            monthly_df=monthly_df,
            annual_df=annual_df,
            quality_report=quality_report,
            location_name=controls["location_name"],
            lat=controls["lat"],
            lon=controls["lon"],
            biome=controls["biome"],
            start_year=controls["start_year"],
            end_year=controls["end_year"]
        )

    elif page == "📚 Data Sources & Methodology":
        render_methodology_page()

    elif page == "👥 About CodeRex":
        render_about_page()

    # Scientific Report Generator in Footer Expander
    st.markdown("---")
    with st.expander("📄 Export Complete Scientific Investigation Dossier (Markdown / HTML)"):
        st.caption("Generate a complete, reproducible scientific report containing methodology, observations, equations, and attribution boundaries.")

        if not daily_df.empty:
            from earthscope.analysis.descriptive_stats import compute_descriptive_stats
            from earthscope.analysis.trend_analysis import linear_regression_trend, mann_kendall_test
            from earthscope.analysis.uncertainty import evaluate_series_uncertainty

            stats_dict = {}
            trends_dict = {}
            mk_dict = {}
            unc_dict = {}

            for var in [c for c in daily_df.columns if c in PARAMETERS_META]:
                s = daily_df[var].dropna()
                stats_dict[var] = compute_descriptive_stats(s, var)
                trends_dict[var] = linear_regression_trend(s)
                mk_dict[var] = mann_kendall_test(s)
                unc_dict[var] = evaluate_series_uncertainty(daily_df[var], var)

            report_md = generate_markdown_report(
                location_name=controls["location_name"],
                lat=controls["lat"],
                lon=controls["lon"],
                start_year=controls["start_year"],
                end_year=controls["end_year"],
                stats_dict=stats_dict,
                trend_dict=trends_dict,
                mk_dict=mk_dict,
                uncertainty_dict=unc_dict,
                retrieval_metadata=ret_meta
            )

            report_html = generate_html_report(report_md, controls["location_name"])

            col_rep1, col_rep2 = st.columns(2)
            with col_rep1:
                st.download_button(
                    label="📥 Download Formal Report (Markdown .md)",
                    data=report_md.encode("utf-8"),
                    file_name=f"EarthScope_Report_{controls['location_name'].replace(' ', '_')}.md",
                    mime="text/markdown",
                    width="stretch"
                )
            with col_rep2:
                st.download_button(
                    label="🖨️ Download Print-Ready Report (HTML)",
                    data=report_html.encode("utf-8"),
                    file_name=f"EarthScope_Report_{controls['location_name'].replace(' ', '_')}.html",
                    mime="text/html",
                    width="stretch"
                )


if __name__ == "__main__":
    main()
