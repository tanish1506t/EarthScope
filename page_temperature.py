"""
Temperature Explorer Page for EarthScope
"""

from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd
import numpy as np

from earthscope.config import PARAMETERS_META
from earthscope.visualizations.charts import (
    plot_timeseries_with_trend,
    plot_temperature_envelope,
    plot_monthly_climatology,
    plot_monthly_anomalies,
    plot_distribution_histogram
)
from earthscope.data.aggregation import calculate_climatology, calculate_anomalies
from earthscope.analysis.descriptive_stats import compute_descriptive_stats
from earthscope.analysis.trend_analysis import linear_regression_trend
from earthscope.components.cards import render_metric_card_html, render_alert_callout


def convert_temp(series: pd.Series, to_unit: str) -> pd.Series:
    """Converts Celsius series to Fahrenheit or Kelvin."""
    if to_unit == "°F":
        return series * 9.0 / 5.0 + 32.0
    elif to_unit == "K":
        return series + 273.15
    return series


def render_temperature_page(
    df: pd.DataFrame,
    monthly_df: pd.DataFrame,
    annual_df: pd.DataFrame,
    location_name: str,
    lat: float,
    lon: float,
    start_year: int,
    end_year: int
) -> None:
    """
    Renders the Temperature Explorer page.
    """
    st.markdown("### 🌡️ Surface Air Temperature Investigation")

    if df.empty or "T2M" not in df.columns:
        st.warning("Temperature parameters (T2M, T2M_MAX, T2M_MIN) are not available for this query.")
        return

    # Top Controls: Unit & Variable Selection
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1.5, 1.5, 1.0])
    with ctrl_col1:
        temp_var = st.selectbox(
            "Target Temperature Metric",
            options=["T2M (Mean Air Temp)", "T2M_MAX (Maximum Temp)", "T2M_MIN (Minimum Temp)", "TS (Skin Surface Temp)"],
            index=0
        )
        var_key = temp_var.split()[0]
    with ctrl_col2:
        unit_choice = st.radio("Display Temperature Unit", ["°C", "°F", "K"], horizontal=True)
    with ctrl_col3:
        baseline_period = st.selectbox("Climatology Baseline", ["All Available Years", "First 5 Years (Historical)"], index=0)

    # Unit conversion copy
    plot_df = df.copy()
    plot_m_df = monthly_df.copy()

    for col in ["T2M", "T2M_MAX", "T2M_MIN", "TS"]:
        if col in plot_df.columns:
            plot_df[col] = convert_temp(plot_df[col], unit_choice)
        if col in plot_m_df.columns:
            plot_m_df[col] = convert_temp(plot_m_df[col], unit_choice)

    # Key Stat Cards
    s_s = plot_df[var_key].dropna() if var_key in plot_df.columns else pd.Series(dtype=float)
    if not s_s.empty:
        stats = compute_descriptive_stats(s_s, var_key)
        reg = linear_regression_trend(s_s)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.html(render_metric_card_html("Historical Mean", f"{stats['mean']:.1f} {unit_choice}", f"Median: {stats['median']:.1f} {unit_choice}", icon="🌡️"))
        with c2:
            rate = reg.get("slope_per_decade", 0.0)
            st.html(render_metric_card_html("Decadal Trend", f"{rate:+.2f} {unit_choice}/dec", f"p-value: {reg.get('p_value', 1.0):.4f}", icon="📈", delta=reg.get("direction", ""), delta_color="positive" if rate > 0 else "negative"))
        with c3:
            st.html(render_metric_card_html("Record Low", f"{stats['min']:.1f} {unit_choice}", f"Date: {stats['min_date']}", icon="❄️", delta="Historical Min", delta_color="neutral"))
        with c4:
            st.html(render_metric_card_html("Record High", f"{stats['max']:.1f} {unit_choice}", f"Date: {stats['max_date']}", icon="🔥", delta="Historical Max", delta_color="neutral"))

    st.markdown("---")

    # Section 1: Diurnal Temperature Envelope
    st.markdown("#### 🌗 Diurnal Thermal Envelope (Daily Mean, Minimum & Maximum)")
    st.caption("Visualizes the continuous temperature envelope bounded by nocturnal minimums (T2M_MIN) and daytime peak solar heating (T2M_MAX).")
    fig_env = plot_temperature_envelope(plot_df)
    st.plotly_chart(fig_env)

    # Section 2: Diurnal Temperature Range (DTR) Analysis
    if "T2M_MAX" in plot_df.columns and "T2M_MIN" in plot_df.columns:
        st.markdown("#### 🌗 Diurnal Temperature Range (DTR = Tmax - Tmin)")
        st.caption("DTR is a fundamental climate indicator. A narrowing DTR often indicates nights warming faster than days due to cloud cover or greenhouse radiative trapping.")
        dtr_df = plot_df.copy()
        dtr_df["DTR"] = dtr_df["T2M_MAX"] - dtr_df["T2M_MIN"]
        fig_dtr = plot_timeseries_with_trend(dtr_df, "DTR", show_rolling=True, show_trend=True, rolling_window=30)
        st.plotly_chart(fig_dtr)

    # Section 3: Monthly Climatology and Anomalies
    st.markdown("#### 📅 Seasonal Climatological Normal & Monthly Departures")
    b_start, b_end = (start_year, start_year + 4) if baseline_period == "First 5 Years (Historical)" else (None, None)
    clim = calculate_climatology(plot_m_df, baseline_start=b_start, baseline_end=b_end)
    anom = calculate_anomalies(plot_m_df, clim)

    col_a, col_b = st.columns(2)
    with col_a:
        fig_clim = plot_monthly_climatology(clim, var_key)
        st.plotly_chart(fig_clim)
    with col_b:
        fig_anom = plot_monthly_anomalies(anom, var_key)
        st.plotly_chart(fig_anom)

    # Section 4: Distribution and Extreme Days
    st.markdown("#### 🔬 Statistical Frequency Distribution & Percentiles")
    d_col1, d_col2 = st.columns([1.5, 1.0])
    with d_col1:
        fig_dist = plot_distribution_histogram(s_s, var_key)
        st.plotly_chart(fig_dist)
    with d_col2:
        st.markdown("##### Distribution Quantiles")
        q_data = {
            "Percentile": ["10th Percentile (Cool Extremes)", "25th Percentile (Q1)", "Median (50th)", "75th Percentile (Q3)", "90th Percentile (Warm Extremes)", "Interquartile Range (IQR)"],
            "Value": [f"{stats['p10']:.1f} {unit_choice}", f"{stats['q25']:.1f} {unit_choice}", f"{stats['median']:.1f} {unit_choice}", f"{stats['q75']:.1f} {unit_choice}", f"{stats['p90']:.1f} {unit_choice}", f"{stats['iqr']:.1f} {unit_choice}"]
        }
        st.table(pd.DataFrame(q_data))

        # Extreme threshold counts in Celsius
        orig_s = df["T2M_MAX"].dropna() if "T2M_MAX" in df.columns else pd.Series(dtype=float)
        if not orig_s.empty:
            hot_35 = int((orig_s >= 35.0).sum())
            hot_40 = int((orig_s >= 40.0).sum())
            frost_0 = int((df["T2M_MIN"].dropna() <= 0.0).sum()) if "T2M_MIN" in df.columns else 0
            st.html(f"""
            <div style="font-size: 12px; color: #cbd5e1; background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #1e293b;">
                <strong>Extreme Event Counts:</strong><br>
                • Days Tmax ≥ 35 °C: <strong>{hot_35:,}</strong><br>
                • Days Tmax ≥ 40 °C: <strong>{hot_40:,}</strong><br>
                • Frost Days Tmin ≤ 0 °C: <strong>{frost_0:,}</strong>
            </div>
            """)
