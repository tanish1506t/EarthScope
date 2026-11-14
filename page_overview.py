"""
Overview Dashboard Page for EarthScope
"""

from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

from earthscope.config import PARAMETERS_META
from earthscope.components.cards import render_metric_card_html, render_alert_callout
from earthscope.components.three_earth import render_three_earth_html
from earthscope.visualizations.charts import (
    plot_timeseries_with_trend,
    plot_precipitation_analysis
)
from earthscope.analysis.trend_analysis import linear_regression_trend, mann_kendall_test


def render_overview_page(
    df: pd.DataFrame,
    monthly_df: pd.DataFrame,
    annual_df: pd.DataFrame,
    quality_report: Dict[str, Any],
    location_name: str,
    lat: float,
    lon: float,
    biome: str,
    start_year: int,
    end_year: int,
    retrieval_meta: Optional[Dict[str, Any]] = None
) -> None:
    """
    Renders the Overview Dashboard page.
    """
    st.markdown("### 🛰️ Planetary Observation & Trend Synthesis")

    # Hero Row: 3D Earth and Quick Mission Brief
    col_3d, col_brief = st.columns([1.2, 1.0])

    with col_3d:
        three_html = render_three_earth_html(lat, lon, location_name, height=340)
        components.html(three_html, height=350, scrolling=False)

    with col_brief:
        st.html(f"""
        <div style="
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 18px 20px;
            height: 310px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        ">
            <div>
                <div style="font-size: 11px; font-weight: 700; color: #00f0ff; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px;">
                    MISSION STATUS: ACTIVE INVESTIGATION
                </div>
                <div style="font-size: 20px; font-weight: 700; color: #f8fafc; margin-bottom: 8px;">
                    {location_name}
                </div>
                <div style="font-size: 12px; color: #94a3b8; margin-bottom: 12px;">
                    <strong>Biome:</strong> {biome}<br>
                    <strong>Coordinates:</strong> {lat:.4f}°N, {lon:.4f}°E<br>
                    <strong>Temporal Window:</strong> {start_year}–{end_year} ({quality_report.get('total_days', 0):,} days)
                </div>
                <p style="font-size: 13px; color: #cbd5e1; line-height: 1.5; margin: 0;">
                    Investigate authentic satellite and modern reanalysis records. EarthScope detects
                    statistically significant trajectories, isolates natural cycles from persistent drift,
                    and quantifies observational uncertainty.
                </p>
            </div>
            <div style="font-size: 11px; color: #64748b; border-top: 1px solid #1e293b; padding-top: 8px;">
                Platform: NASA POWER API v2 (Agroclimatology / MERRA-2 FP-IT)
            </div>
        </div>
        """)

    st.markdown("---")

    # Key Scientific Metrics Row
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    # 1. Mean Temperature
    t2m_s = df["T2M"].dropna() if "T2M" in df.columns else pd.Series(dtype=float)
    if not t2m_s.empty:
        t2m_mean = t2m_s.mean()
        reg_t2m = linear_regression_trend(t2m_s)
        rate = reg_t2m.get("slope_per_decade", 0.0)
        rate_sign = "+" if rate > 0 else ""
        delta_str = f"{rate_sign}{rate:.2f} °C/dec"
        d_color = "positive" if rate > 0 else ("negative" if rate < 0 else "neutral")
        card_t2m = render_metric_card_html(
            title="Mean Air Temp (2m)",
            value=f"{t2m_mean:.1f} °C",
            subtitle=f"Range: {t2m_s.min():.1f} to {t2m_s.max():.1f} °C",
            delta=delta_str,
            delta_color=d_color,
            icon="🌡️",
            border_color="rgba(0, 240, 255, 0.4)"
        )
    else:
        card_t2m = render_metric_card_html("Mean Air Temp", "N/A", "Data unavailable", icon="🌡️")

    # 2. Total Precipitation
    p_s = df["PRECTOTCORR"].dropna() if "PRECTOTCORR" in df.columns else pd.Series(dtype=float)
    if not p_s.empty:
        years_span = max(1, end_year - start_year + 1)
        annual_avg_rain = p_s.sum() / years_span
        rain_days = int((p_s >= 0.1).sum())
        rain_days_pct = round(rain_days / len(p_s) * 100.0, 1)
        card_precip = render_metric_card_html(
            title="Annual Mean Precip",
            value=f"{annual_avg_rain:.0f} mm/yr",
            subtitle=f"{rain_days_pct}% rainy days (≥0.1mm)",
            delta=f"Max: {p_s.max():.1f} mm/d",
            delta_color="neutral",
            icon="🌧️",
            border_color="rgba(16, 185, 129, 0.4)"
        )
    else:
        card_precip = render_metric_card_html("Annual Precip", "N/A", "Data unavailable", icon="🌧️")

    # 3. Data Completeness
    tot_days = quality_report.get("total_days", 0)
    t2m_vars = quality_report.get("variables", {}).get("T2M", {})
    valid_obs = t2m_vars.get("valid_observations", len(t2m_s))
    missing_pct = t2m_vars.get("missing_percentage", 0.0)
    card_data = render_metric_card_html(
        title="Usable Records",
        value=f"{valid_obs:,}",
        subtitle=f"{missing_pct}% fill value (-999) masked",
        delta=f"{100.0 - missing_pct:.1f}% valid",
        delta_color="positive" if missing_pct < 5.0 else "neutral",
        icon="🛰️",
        border_color="rgba(56, 189, 248, 0.4)"
    )

    # 4. Statistical Trend Verdict
    if not t2m_s.empty and len(t2m_s) >= 10:
        mk = mann_kendall_test(t2m_s)
        p_val = mk.get("p_value", 1.0)
        is_sig = mk.get("is_significant", False)
        trend_name = mk.get("trend", "no_trend")

        if is_sig:
            trend_val = "Warming" if trend_name == "increasing" else "Cooling"
            v_sub = f"p = {p_val:.4f} (Significant)"
            v_color = "positive" if trend_name == "increasing" else "negative"
        else:
            trend_val = "Stable / Noise"
            v_sub = f"p = {p_val:.3f} (Natural cycle)"
            v_color = "neutral"

        card_verdict = render_metric_card_html(
            title="Mann-Kendall Trend",
            value=trend_val,
            subtitle=v_sub,
            delta=f"Z = {mk.get('z_statistic', 0.0):.2f}",
            delta_color=v_color,
            icon="🔬",
            border_color="rgba(245, 158, 11, 0.4)"
        )
    else:
        card_verdict = render_metric_card_html("Trend Verdict", "Evaluating", "Awaiting sufficient records", icon="🔬")

    with m_col1:
        st.html(card_t2m)
    with m_col2:
        st.html(card_precip)
    with m_col3:
        st.html(card_data)
    with m_col4:
        st.html(card_verdict)

    st.markdown("---")

    # Primary Visualizations Row
    st.markdown("#### 📈 Key Environmental Trajectories")
    c1, c2 = st.columns(2)

    with c1:
        fig_t = plot_timeseries_with_trend(df, "T2M", show_rolling=True, show_trend=True, show_ci=True, rolling_window=30)
        st.plotly_chart(fig_t)

    with c2:
        fig_p = plot_precipitation_analysis(df, monthly_df)
        st.plotly_chart(fig_p)

    # Informational Callout
    callout_html = render_alert_callout(
        f"<strong>Scientific Quality Assurance:</strong> Records for {location_name} are calibrated using NASA's MERRA-2 modern reanalysis. "
        f"Missing values (flagged as -999.0 by NASA) are strictly preserved as NaNs and never interpolated with synthetic values. "
        f"Explore the specialized modules in the sidebar for in-depth statistical hypothesis testing and anomaly analyses.",
        level="info"
    )
    st.html(callout_html)
