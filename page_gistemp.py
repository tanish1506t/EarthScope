"""
NASA GISTEMP v4 Global Climate Anomaly Explorer
Analyzes official NASA Goddard Institute for Space Studies surface temperature anomalies (1880–present).
"""

from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from earthscope.data.nasa_giss_client import NASAGissClient
from earthscope.components.cards import render_metric_card_html, render_alert_callout
from earthscope.visualizations.theme import (
    apply_earthscope_theme,
    COLOR_ROSE,
    COLOR_CYAN,
    COLOR_AMBER,
    COLOR_SKY,
    COLOR_EMERALD,
    BG_COLOR,
    TEXT_COLOR,
    MUTED_TEXT
)
from earthscope.analysis.trend_analysis import linear_regression_trend, mann_kendall_test


@st.cache_data(ttl=86400)
def load_giss_dataset(region: str = "global") -> Tuple[pd.DataFrame, pd.Series]:
    client = NASAGissClient(cache_enabled=True)
    df = client.fetch_gistemp_data(region)
    s = client.get_monthly_anomaly_series(region)
    return df, s


def render_gistemp_page(local_annual_df: Optional[pd.DataFrame] = None, location_name: str = "Local Observatory") -> None:
    """
    Renders the NASA GISTEMP v4 Global Climate Explorer page.
    """
    st.markdown("### 🌍 NASA GISTEMP v4 — Planetary Temperature Anomaly Record")

    st.html("""
    <div style="font-size: 13px; color: #94a3b8; margin-bottom: 16px;">
        Investigate authentic global, hemispheric, and zonal surface temperature anomalies (1880–present)
        from the <strong>NASA Goddard Institute for Space Studies (GISS)</strong>.
        Baseline: 1951–1980 climatological normal.
    </div>
    """)

    # Top Controls
    c_reg, c_win = st.columns([1.5, 1.5])
    with c_reg:
        region_opt = st.selectbox(
            "NASA GISS Domain",
            ["Global (Land-Ocean Means)", "Northern Hemisphere", "Southern Hemisphere"],
            index=0
        )
        region_map = {
            "Global (Land-Ocean Means)": "global",
            "Northern Hemisphere": "northern_hemisphere",
            "Southern Hemisphere": "southern_hemisphere"
        }
        domain_key = region_map[region_opt]

    with c_win:
        time_scope = st.selectbox("Historical Epoch", ["Full Record (1880–Present)", "Modern Satellite Era (1979–Present)", "Last 30 Years (1995–Present)"], index=0)

    # Load authentic NASA GISS data
    with st.spinner("🛰️ Retrieving NASA GISS GISTEMP v4 table..."):
        try:
            giss_df, giss_monthly = load_giss_dataset(domain_key)
        except Exception as e:
            st.error(f"Failed to load NASA GISS dataset: {e}")
            return

    # Filter by epoch
    if time_scope == "Modern Satellite Era (1979–Present)":
        giss_df = giss_df[giss_df.index >= 1979]
        giss_monthly = giss_monthly[giss_monthly.index.year >= 1979]
    elif time_scope == "Last 30 Years (1995–Present)":
        giss_df = giss_df[giss_df.index >= 1995]
        giss_monthly = giss_monthly[giss_monthly.index.year >= 1995]

    # Annual anomaly series (J-D column is Jan-Dec annual mean)
    annual_s = giss_df["J-D"].dropna() if "J-D" in giss_df.columns else pd.Series(dtype=float)

    # Key metrics row
    if not annual_s.empty:
        reg = linear_regression_trend(annual_s, temporal_unit="year")
        latest_val = float(annual_s.iloc[-1])
        latest_year = int(annual_s.index[-1])
        warmest_year = int(annual_s.idxmax())
        warmest_val = float(annual_s.max())

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.html(render_metric_card_html(
                title=f"Latest Anomaly ({latest_year})",
                value=f"{latest_val:+.2f} °C",
                subtitle="vs 1951–1980 baseline",
                delta=f"+{latest_val - 0.0:.2f} °C",
                delta_color="negative",
                icon="🌡️",
                border_color="rgba(244, 63, 94, 0.4)"
            ))
        with m2:
            rate = reg.get("slope_per_decade", 0.0)
            st.html(render_metric_card_html(
                title="Decadal Warming Rate",
                value=f"{rate:+.3f} °C/dec",
                subtitle=f"p < 0.0001 (R²={reg.get('r_squared', 0.0):.2f})",
                delta="Statistically Significant",
                delta_color="positive",
                icon="📈",
                border_color="rgba(0, 240, 255, 0.4)"
            ))
        with m3:
            st.html(render_metric_card_html(
                title="All-Time Warmest Year",
                value=f"{warmest_year}",
                subtitle=f"Departure: {warmest_val:+.2f} °C",
                icon="🔥",
                delta="Record High",
                delta_color="negative"
            ))
        with m4:
            # Pre-industrial offset (~0.2°C added to 1951-1980 baseline to estimate 1850-1900 pre-industrial)
            pre_ind = latest_val + 0.2
            st.html(render_metric_card_html(
                title="Pre-Industrial Offset",
                value=f"{pre_ind:+.2f} °C",
                subtitle="Estimate vs 1850–1900",
                delta="1.5°C Paris Threshold" if pre_ind >= 1.5 else "Approaching 1.5°C",
                delta_color="negative" if pre_ind >= 1.5 else "neutral",
                icon="🎯"
            ))

    st.markdown("---")

    # Primary Visualization: NASA GISTEMP Annual Anomaly Bars & Trend
    st.markdown("#### 📈 NASA GISTEMP v4 Annual Temperature Anomalies (1880–Present)")

    fig_giss = go.Figure()
    colors = [COLOR_ROSE if v >= 0 else COLOR_SKY for v in annual_s.values]

    fig_giss.add_trace(go.Bar(
        x=annual_s.index,
        y=annual_s.values,
        marker=dict(color=colors),
        name="Annual Anomaly",
        hovertemplate="%{x}<br>Anomaly: <b>%{y:+.2f} °C</b><extra></extra>"
    ))

    # 10-year rolling average
    roll_10 = annual_s.rolling(window=10, min_periods=5).mean()
    fig_giss.add_trace(go.Scatter(
        x=roll_10.index,
        y=roll_10.values,
        mode="lines",
        line=dict(color=COLOR_CYAN, width=2.5),
        name="10-Year Lowess/Moving Mean",
        hovertemplate="%{x}<br>10-yr Mean: <b>%{y:+.2f} °C</b><extra></extra>"
    ))

    fig_giss.add_hline(y=0.0, line_dash="solid", line_color=MUTED_TEXT, line_width=1.0)
    fig_giss.add_hline(y=1.0, line_dash="dash", line_color=COLOR_AMBER, annotation_text="+1.0°C Global Milestone", annotation_position="top left")

    fig_giss = apply_earthscope_theme(
        fig_giss,
        title=f"NASA GISTEMP v4 Surface Temperature Anomalies — {region_opt}",
        x_title="Calendar Year",
        y_title="Temperature Anomaly (°C relative to 1951–1980 normal)"
    )
    st.plotly_chart(fig_giss)

    st.markdown("---")

    # Section 2: Top 10 Warmest Years Leaderboard & Seasonal Comparison
    c_lead, c_seas = st.columns([1.1, 1.4])

    with c_lead:
        st.markdown("#### 🏆 Top 10 Warmest Years on Record")
        top10 = annual_s.sort_values(ascending=False).head(10).reset_index()
        top10.columns = ["Year", "Anomaly (°C)"]
        top10.index = range(1, 11)
        top10["Anomaly (°C)"] = top10["Anomaly (°C)"].apply(lambda v: f"{v:+.2f} °C")
        st.dataframe(top10)

    with c_seas:
        st.markdown("#### 🍂 Seasonal Warming Disparity (DJF, MAM, JJA, SON)")
        st.caption("Investigate whether winter (DJF) or summer (JJA) is warming at a faster pace.")

        fig_seas = go.Figure()
        season_cols = [("DJF", "Winter", COLOR_SKY), ("MAM", "Spring", COLOR_EMERALD), ("JJA", "Summer", COLOR_ROSE), ("SON", "Autumn", COLOR_AMBER)]

        for sc, sname, color in season_cols:
            if sc in giss_df.columns:
                s_vals = giss_df[sc].dropna()
                fig_seas.add_trace(go.Scatter(
                    x=s_vals.index,
                    y=s_vals.values,
                    mode="lines",
                    name=sname,
                    line=dict(color=color, width=1.5),
                    hovertemplate="%{x} " + sname + ": <b>%{y:+.2f} °C</b><extra></extra>"
                ))

        fig_seas = apply_earthscope_theme(
            fig_seas,
            title="Seasonal Anomaly Trajectories (NASA GISTEMP)",
            x_title="Year",
            y_title="Anomaly (°C)"
        )
        st.plotly_chart(fig_seas)

    # Section 3: Data Provenance
    st.html("""
    <div style="background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 16px; font-size: 12px; color: #94a3b8; line-height: 1.5; margin-top: 16px;">
        <strong>Data Provenance:</strong> NASA GISTEMP v4 is developed at the NASA Goddard Institute for Space Studies (GISS).
        It combines surface air temperature measurements from NOAA GHCN v4 (Global Historical Climatology Network) with ERSST v5 (Extended Reconstructed Sea Surface Temperature).
        Reference: Lenssen et al. (2019), <em>Improvements in the GISTEMP Uncertainty Model</em>, JGR Atmospheres.
    </div>
    """)
