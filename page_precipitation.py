"""
Precipitation Explorer Page for EarthScope
"""

from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from earthscope.config import PARAMETERS_META
from earthscope.visualizations.charts import (
    plot_precipitation_analysis,
    plot_monthly_climatology,
    plot_monthly_anomalies
)
from earthscope.data.aggregation import calculate_climatology, calculate_anomalies
from earthscope.analysis.descriptive_stats import compute_descriptive_stats
from earthscope.analysis.trend_analysis import linear_regression_trend
from earthscope.components.cards import render_metric_card_html, render_alert_callout
from earthscope.visualizations.theme import (
    apply_earthscope_theme,
    COLOR_EMERALD,
    COLOR_CYAN,
    COLOR_AMBER,
    COLOR_ROSE,
    COLOR_SKY
)


def render_precipitation_page(
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
    Renders the Precipitation Explorer page.
    """
    st.markdown("### 🌧️ Hydrological Dynamics & Precipitation Investigation")

    if df.empty or "PRECTOTCORR" not in df.columns:
        st.warning("Precipitation parameter (PRECTOTCORR) is unavailable for this query.")
        return

    p_s = df["PRECTOTCORR"].dropna()
    total_days = len(p_s)
    years_span = max(1, end_year - start_year + 1)
    tot_precip = p_s.sum()
    annual_mean = tot_precip / years_span

    # Descriptive metrics
    p_stats = compute_descriptive_stats(p_s, "PRECTOTCORR")

    # Metrics row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.html(render_metric_card_html("Annual Average Rain", f"{annual_mean:.0f} mm/yr", f"Total: {tot_precip:,.0f} mm over {years_span} yrs", icon="💧", border_color="rgba(16, 185, 129, 0.4)"))
    with c2:
        rain_days_pct = p_stats.get("rain_days_pct", 0.0)
        st.html(render_metric_card_html("Rain Days (≥0.1mm)", f"{p_stats.get('rain_days_count', 0):,} days", f"{rain_days_pct}% of calendar days", icon="🌧️", delta=f"{rain_days_pct}% frequency", delta_color="neutral"))
    with c3:
        st.html(render_metric_card_html("Single-Day Peak", f"{p_s.max():.1f} mm", f"Date: {p_stats.get('max_date', '')}", icon="⛈️", delta="Max 24h Flux", delta_color="negative"))
    with c4:
        st.html(render_metric_card_html("Longest Dry Spell", f"{p_stats.get('longest_dry_spell_days', 0)} days", "Consecutive days < 0.1 mm", icon="☀️", delta="Drought Metric", delta_color="neutral"))

    st.markdown("---")

    # Section 1: Daily Events and Cumulative Curves
    st.markdown("#### 🌊 Daily Rainfall Events & Multi-Year Cumulative Mass Accumulation")
    fig_precip = plot_precipitation_analysis(df, monthly_df)
    st.plotly_chart(fig_precip)

    # Section 2: Annual Precipitation Totals
    st.markdown("#### 📊 Annual Rainfall Totals Comparison")
    if not annual_df.empty and "PRECTOTCORR" in annual_df.columns:
        ann_p = annual_df["PRECTOTCORR"].dropna()
        if not ann_p.empty:
            mean_annual = float(ann_p.mean())
            colors = [COLOR_EMERALD if val >= mean_annual else COLOR_AMBER for val in ann_p.values]

            fig_ann = go.Figure()
            fig_ann.add_trace(go.Bar(
                x=ann_p.index,
                y=ann_p.values,
                marker=dict(color=colors),
                name="Annual Total",
                hovertemplate="%{x}<br>Rainfall: <b>%{y:.1f} mm</b><extra></extra>"
            ))
            fig_ann.add_hline(y=mean_annual, line_dash="dash", line_color=COLOR_CYAN,
                              annotation_text=f"Baseline Mean: {mean_annual:.1f} mm", annotation_position="top left")

            fig_ann = apply_earthscope_theme(
                fig_ann,
                title="Year-over-Year Total Precipitation Accumulation",
                x_title="Calendar Year",
                y_title="Total Precipitation (mm/year)"
            )
            st.plotly_chart(fig_ann)

    # Section 3: Rainfall Intensity Spectrum
    st.markdown("#### ⚡ Rainfall Intensity Spectrum & Spell Classification")
    col_spec1, col_spec2 = st.columns(2)

    with col_spec1:
        # Intensity bins
        dry_cnt = int((p_s < 0.1).sum())
        light_cnt = int(((p_s >= 0.1) & (p_s < 5.0)).sum())
        mod_cnt = int(((p_s >= 5.0) & (p_s < 15.0)).sum())
        heavy_cnt = int(((p_s >= 15.0) & (p_s < 30.0)).sum())
        ext_cnt = int((p_s >= 30.0).sum())

        labels = ["Dry (<0.1 mm)", "Light (0.1–5 mm)", "Moderate (5–15 mm)", "Heavy (15–30 mm)", "Extreme (>30 mm)"]
        counts = [dry_cnt, light_cnt, mod_cnt, heavy_cnt, ext_cnt]
        slice_colors = ["#334155", COLOR_SKY, COLOR_CYAN, COLOR_EMERALD, COLOR_ROSE]

        fig_pie = go.Figure(go.Pie(
            labels=labels,
            values=counts,
            hole=0.45,
            marker=dict(colors=slice_colors),
            textinfo="percent+label",
            hoverinfo="value+percent"
        ))
        fig_pie.update_layout(
            paper_bgcolor="#081226",
            plot_bgcolor="#081226",
            font=dict(color="#f8fafc"),
            title=dict(text="<b>Precipitation Daily Intensity Breakdown</b>", font=dict(color="#f8fafc", size=14)),
            height=340,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_pie)

    with col_spec2:
        st.html("""
        <div style="background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 18px; font-size: 13px; color: #cbd5e1; line-height: 1.6;">
            <div style="font-weight: 700; color: #10b981; margin-bottom: 8px;">🛰️ SATELLITE VS GROUND STATION OBSERVATION</div>
            <p style="margin: 0 0 10px 0;">
                The parameter <strong>PRECTOTCORR</strong> is a bias-corrected precipitation estimate derived from NASA's
                Goddard Earth Observing System (GEOS) atmospheric assimilation model, integrated with satellite radar/radiometer soundings
                and GPCP (Global Precipitation Climatology Project) calibrations.
            </p>
            <div style="background: rgba(16, 185, 129, 0.1); border-left: 2px solid #10b981; padding: 8px 12px; margin-bottom: 10px; border-radius: 0 6px 6px 0;">
                <strong>Key Interpretation Rule:</strong> Satellite estimates represent area-averaged fluxes across a grid cell (~0.5° × 0.5°),
                which can smooth localized convective cloudbursts relative to direct physical tipping-bucket rain gauges.
            </div>
            <p style="margin: 0; font-size: 12px; color: #94a3b8;">
                Dry spell analysis identifies prolonged meteorological drought risks, vital for agricultural and reservoir planning.
            </p>
        </div>
        """)
