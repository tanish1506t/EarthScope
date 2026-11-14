"""
Trend Analysis Lab Page for EarthScope
Deep statistical detective workbench with OLS regression, Mann-Kendall test,
Sen's slope, autocorrelation adjustments, and two-period comparisons.
"""

from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd
import numpy as np

from earthscope.config import PARAMETERS_META, SIGNIFICANCE_ALPHA
from earthscope.visualizations.charts import plot_timeseries_with_trend
from earthscope.analysis.trend_analysis import (
    linear_regression_trend,
    mann_kendall_test,
    compare_two_periods
)
from earthscope.analysis.uncertainty import evaluate_series_uncertainty
from earthscope.components.cards import render_metric_card_html, render_alert_callout


def render_trend_lab_page(
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
    Renders the Trend Analysis Lab page.
    """
    st.markdown("### 🔬 Trend Analysis Lab & Statistical Detective Workbench")

    st.html("""
    <div style="font-size: 13px; color: #94a3b8; margin-bottom: 16px;">
        Perform hypothesis testing, quantify empirical rates of change, evaluate serial autocorrelation,
        and test whether observed trajectories exceed natural climate variability.
    </div>
    """)

    # Workbench Controls
    col_var, col_agg, col_roll = st.columns([1.5, 1.2, 1.3])

    available_vars = [c for c in df.columns if c in PARAMETERS_META]
    if not available_vars:
        st.warning("No standard parameters available for analysis.")
        return

    with col_var:
        selected_var = st.selectbox(
            "Investigation Variable",
            options=available_vars,
            format_func=lambda v: f"{v} — {PARAMETERS_META.get(v, {}).get('name', v)}"
        )
    with col_agg:
        agg_choice = st.selectbox("Temporal Granularity", ["Daily", "Monthly", "Annual"], index=0)
    with col_roll:
        roll_window = st.slider("Smoothing Window (Steps)", min_value=7, max_value=180, value=30, step=7)

    # Select proper DataFrame
    if agg_choice == "Monthly":
        active_df = monthly_df
    elif agg_choice == "Annual":
        active_df = annual_df
    else:
        active_df = df

    meta = PARAMETERS_META.get(selected_var, {})
    units = meta.get("units", "")
    readable_name = meta.get("name", selected_var)

    if selected_var not in active_df.columns:
        st.info(f"Variable {selected_var} is not present in the {agg_choice} dataset.")
        return

    series = active_df[selected_var].dropna()
    if series.empty:
        st.warning(f"No valid observations for {selected_var} in {agg_choice} view.")
        return

    # Visual Time Series
    st.markdown(f"#### 📈 {readable_name} Time Series & OLS Fit ({agg_choice})")
    fig_lab = plot_timeseries_with_trend(
        active_df,
        selected_var,
        show_rolling=True,
        show_trend=True,
        show_ci=True,
        rolling_window=roll_window
    )
    st.plotly_chart(fig_lab)

    st.markdown("---")

    # Run Statistical Tests
    reg = linear_regression_trend(series)
    mk = mann_kendall_test(series)
    unc = evaluate_series_uncertainty(series, selected_var)

    # Top Statistical Summary Cards
    st.markdown("#### 🧪 Dual-Method Hypothesis Testing Results")
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        rate = reg.get("slope_per_decade", 0.0)
        st.html(render_metric_card_html(
            title="OLS Decadal Rate",
            value=f"{rate:+.3f} {units}/dec",
            subtitle=f"R²: {reg.get('r_squared', 0.0):.3f}",
            icon="📐",
            delta=reg.get("direction", ""),
            delta_color="positive" if rate > 0 else "negative"
        ))

    with m2:
        ols_p = reg.get("p_value", 1.0)
        is_ols_sig = reg.get("is_significant", False)
        st.html(render_metric_card_html(
            title="OLS p-value",
            value=f"{ols_p:.4f}",
            subtitle="Significant (p < 0.05)" if is_ols_sig else "Not Significant (p ≥ 0.05)",
            icon="🎯",
            delta="α = 0.05",
            delta_color="positive" if is_ols_sig else "neutral"
        ))

    with m3:
        mk_z = mk.get("z_statistic", 0.0)
        st.html(render_metric_card_html(
            title="Mann-Kendall Z",
            value=f"{mk_z:.2f}",
            subtitle=f"p-val: {mk.get('p_value', 1.0):.4f}",
            icon="📊",
            delta=mk.get("trend", "no_trend"),
            delta_color="positive" if mk.get("is_significant") else "neutral"
        ))

    with m4:
        sens_s = mk.get("sens_slope", 0.0)
        st.html(render_metric_card_html(
            title="Sen's Median Slope",
            value=f"{sens_s:.4f} {units}",
            subtitle="Outlier-robust slope",
            icon="⚖️",
            border_color="rgba(168, 85, 247, 0.4)"
        ))

    # Method Comparison Table
    st.markdown("##### Detailed Comparison of Parametric vs Non-Parametric Estimators")
    table_data = {
        "Metric / Property": [
            "Method Type",
            "Underlying Assumption",
            "Rate of Change",
            "Test Statistic",
            "p-value",
            "Statistical Significance (α=0.05)",
            "Robustness to Extreme Outliers"
        ],
        "Parametric OLS Linear Regression": [
            "Ordinary Least Squares",
            "Normally distributed residuals, homoscedasticity",
            f"{reg.get('slope_per_decade', 0.0):+.3f} {units} / decade",
            f"t = {reg.get('slope', 0.0) / (reg.get('std_error', 1e-5) if reg.get('std_error', 0) > 0 else 1.0):.2f}",
            f"{reg.get('p_value', 1.0):.4f}",
            "Significant (p < 0.05)" if reg.get("is_significant") else "Not Significant (p ≥ 0.05)",
            "Sensitive to extreme observational anomalies"
        ],
        "Non-Parametric Mann-Kendall & Sen's Slope": [
            "Rank-based Kendall Tau + Theil-Sen Median",
            "Monotonic trend, no normality assumption required",
            f"{mk.get('sens_slope', 0.0) * 10:+.3f} {units} / decade (Sen's Median)",
            f"Z = {mk.get('z_statistic', 0.0):.2f} (Kendall S = {mk.get('s_statistic', 0)})",
            f"{mk.get('p_value', 1.0):.4f}",
            "Significant (p < 0.05)" if mk.get("is_significant") else "Not Significant (p ≥ 0.05)",
            "High robustness (breakdown point ~29%)"
        ]
    }
    st.table(pd.DataFrame(table_data))

    st.markdown("---")

    # Section: Autocorrelation & Serial Persistence
    st.markdown("#### ⏳ Serial Autocorrelation & Effective Sample Size (N_eff)")
    r1 = unc.get("lag1_autocorrelation", 0.0)
    n_eff = unc.get("effective_sample_size", len(series))

    col_ac1, col_ac2 = st.columns([1.2, 1.8])
    with col_ac1:
        st.html(f"""
        <div style="background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 16px; font-size: 13px;">
            <div style="font-weight: 700; color: #38bdf8; margin-bottom: 6px;">Autocorrelation Metrics</div>
            • Total Observations: <strong>{len(series):,}</strong><br>
            • Lag-1 Autocorrelation (r₁): <strong>{r1:.3f}</strong><br>
            • Effective Sample Size (N_eff): <strong>{n_eff:,}</strong><br>
            • Max Missing Gap: <strong>{unc.get('max_consecutive_gap_days', 0)} days</strong>
        </div>
        """)
    with col_ac2:
        ac_note = unc.get("autocorr_assessment", "")
        callout_level = "warning" if abs(r1) >= 0.3 else "info"
        st.html(render_alert_callout(
            f"<strong>Physical Persistence Analysis:</strong> {ac_note} "
            f"In environmental time series, successive daily or monthly weather states inherit thermal inertia. "
            f"If r₁ is strongly positive, degrees of freedom are reduced from {len(series):,} to approximately {n_eff:,}.",
            level=callout_level
        ))

    st.markdown("---")

    # Section: Period-to-Period Comparison Workbench
    st.markdown("#### ⚖️ Period-to-Period Comparative Diagnosis (e.g. Baseline vs Recent)")
    mid_year = start_year + (end_year - start_year) // 2

    c_p1, c_p2 = st.columns(2)
    with c_p1:
        p_a_start = st.number_input("Period A Start", min_value=start_year, max_value=end_year, value=start_year)
        p_a_end = st.number_input("Period A End", min_value=start_year, max_value=end_year, value=mid_year)
    with c_p2:
        p_b_start = st.number_input("Period B Start", min_value=start_year, max_value=end_year, value=mid_year + 1)
        p_b_end = st.number_input("Period B End", min_value=start_year, max_value=end_year, value=end_year)

    if p_a_start <= p_a_end and p_b_start <= p_b_end and isinstance(df.index, pd.DatetimeIndex):
        comp = compare_two_periods(
            df[selected_var],
            period_a_years=(int(p_a_start), int(p_a_end)),
            period_b_years=(int(p_b_start), int(p_b_end)),
            var_name=selected_var
        )

        if comp.get("status") == "success":
            delta_v = comp["delta"]
            pct_v = comp["pct_change"]
            pct_s = f"({delta_v:+0.2f} {units}, {pct_v:+.1f}%)" if pct_v is not None else ""
            t_stat = comp["t_statistic"]
            p_ttest = comp["p_value"]
            is_sig_t = comp["is_significant"]

            st.html(f"""
            <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid #334155; border-radius: 12px; padding: 18px; margin-top: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 700; color: #00f0ff; font-size: 15px;">
                        Welch's Two-Sample t-Test: {comp['period_a_label']} vs {comp['period_b_label']}
                    </span>
                    <span style="
                        background: {'rgba(16,185,129,0.2)' if is_sig_t else 'rgba(148,163,184,0.2)'};
                        color: {'#10b981' if is_sig_t else '#94a3b8'};
                        padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: 700;
                    ">
                        {'STATISTICALLY SIGNIFICANT SHIFT' if is_sig_t else 'NO SIGNIFICANT SHIFT'}
                    </span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 12px;">
                    <div><span style="color: #94a3b8; font-size: 11px;">PERIOD A MEAN:</span><br><strong>{comp['mean_a']:.2f} {units}</strong></div>
                    <div><span style="color: #94a3b8; font-size: 11px;">PERIOD B MEAN:</span><br><strong>{comp['mean_b']:.2f} {units}</strong></div>
                    <div><span style="color: #94a3b8; font-size: 11px;">NET DEPARTURE:</span><br><strong style="color: {'#f43f5e' if delta_v > 0 else '#38bdf8'};">{delta_v:+.2f} {units} {pct_s}</strong></div>
                    <div><span style="color: #94a3b8; font-size: 11px;">t-STAT & p-VALUE:</span><br><strong>t={t_stat:.2f}, p={p_ttest:.4f}</strong></div>
                </div>
            </div>
            """)

    st.markdown("---")

    # Export Section
    st.markdown("#### 💾 Export Lab Data & Statistical Summary")
    csv_bytes = active_df.to_csv(index=True).encode("utf-8")
    st.download_button(
        label=f"📥 Download {selected_var} ({agg_choice}) Dataset CSV",
        data=csv_bytes,
        file_name=f"earthscope_{location_name.replace(' ', '_')}_{selected_var}_{agg_choice}.csv",
        mime="text/csv"
    )
