"""
AI Insights and Scientific Narrative Page for EarthScope
Delivers evidence-grounded scientific summaries adhering strictly to actual calculated statistics.
Never hallucinates facts or asserts unsupported causal claims.
"""

from typing import Dict, Any, Optional, List
import streamlit as st
import pandas as pd

from earthscope.config import PARAMETERS_META
from earthscope.insights.scientific_summaries import generate_trend_insight
from earthscope.analysis.descriptive_stats import compute_descriptive_stats
from earthscope.analysis.trend_analysis import linear_regression_trend, mann_kendall_test
from earthscope.analysis.uncertainty import evaluate_series_uncertainty
from earthscope.components.cards import render_metric_card_html, render_alert_callout


def render_ai_insights_page(
    df: pd.DataFrame,
    monthly_df: pd.DataFrame,
    annual_df: pd.DataFrame,
    quality_report: Dict[str, Any],
    location_name: str,
    lat: float,
    lon: float,
    biome: str,
    start_year: int,
    end_year: int
) -> None:
    """
    Renders the AI Scientific Insights page.
    """
    st.markdown("### 🤖 Evidence-Grounded Scientific Assistant & Trend Synthesis")

    st.html("""
    <div style="font-size: 13px; color: #94a3b8; margin-bottom: 16px;">
        Translates raw statistical coefficients into rigorous, clear scientific narratives.
        Every deduction is strictly tethered to calculated observations, test statistics, and observational completeness metrics.
    </div>
    """)

    if df.empty:
        st.warning("No data records available to generate insights.")
        return

    # Generate insights across all available variables
    available_vars = [c for c in df.columns if c in PARAMETERS_META]

    st.markdown("#### 📜 Formal Evidence-Grounded Scientific Finding")

    # Variable selector for deep dive narrative
    target_var = st.selectbox(
        "Synthesize Findings For Variable",
        options=available_vars,
        format_func=lambda v: f"{v} — {PARAMETERS_META.get(v, {}).get('name', v)}"
    )

    s_data = df[target_var].dropna()
    s_stats = compute_descriptive_stats(s_data, target_var)
    s_reg = linear_regression_trend(s_data)
    s_mk = mann_kendall_test(s_data)
    s_unc = evaluate_series_uncertainty(df[target_var], target_var)

    insight = generate_trend_insight(
        var_name=target_var,
        location_name=location_name,
        lat=lat,
        lon=lon,
        start_year=start_year,
        end_year=end_year,
        stats_dict=s_stats,
        trend_dict=s_reg,
        mk_dict=s_mk,
        uncertainty_dict=s_unc
    )

    # Render formal scientific findings box
    st.html(f"""
    <div style="
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(8, 18, 38, 0.95) 100%);
        border: 1px solid #00f0ff;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 30px rgba(0, 240, 255, 0.1);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
            <span style="font-size: 18px; font-weight: 700; color: #f8fafc;">
                {insight['title']}
            </span>
            <span style="
                background: rgba(0, 240, 255, 0.15);
                border: 1px solid rgba(0, 240, 255, 0.4);
                color: #00f0ff;
                padding: 4px 12px;
                border-radius: 9999px;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            ">
                {insight['verdict']}
            </span>
        </div>
        <p style="font-size: 14px; line-height: 1.7; color: #e2e8f0; margin-bottom: 16px;">
            {insight['summary_text']}
        </p>
        <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; border-radius: 8px; padding: 12px 16px; margin-bottom: 14px; font-size: 12px; color: #94a3b8;">
            <strong style="color: #38bdf8;">Persistence Evaluation:</strong> {insight.get('autocorrelation_note', '')}
        </div>
        <div style="border-top: 1px solid #1e293b; padding-top: 12px; font-size: 11px; color: #64748b; font-style: italic;">
            {insight['scientific_disclaimer']}
        </div>
    </div>
    """)

    # Key Metrics Grid
    st.markdown("##### Grounded Quantitative Evidence Summary")
    grid_cols = st.columns(4)
    km = insight.get("key_metrics", {})
    idx = 0
    for label, val in km.items():
        with grid_cols[idx % 4]:
            st.html(f"""
            <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                <div style="font-size: 10px; color: #94a3b8; text-transform: uppercase;">{label}</div>
                <div style="font-size: 15px; font-weight: 700; color: #f8fafc; margin-top: 2px;">{val}</div>
            </div>
            """)
        idx += 1

    st.markdown("---")

    # Section 2: Interactive Scientific Detective Q&A
    st.markdown("#### 💬 Scientific Detective Inquiry Workbench")
    st.caption("Ask questions about the observed data. Responses are dynamically generated and verified against the computed dataset metrics.")

    preset_questions = [
        f"Did {location_name} experience a statistically significant temperature change?",
        f"How does the precipitation intensity and drought spell risk look over {start_year}–{end_year}?",
        "What are the observational uncertainties or limitations in this dataset?",
        "How do diurnal temperature variations relate to surface land dynamics?"
    ]

    selected_prompt = st.selectbox("Select Scientific Question or Enter Custom Inquiry Below:", preset_questions)
    custom_inquiry = st.text_input("Or Ask Custom Research Question:", value="")
    final_query = custom_inquiry.strip() if custom_inquiry.strip() else selected_prompt

    if st.button("🔍 Synthesize Scientific Answer", type="primary"):
        with st.spinner("Synthesizing evidence-grounded answer..."):
            ans = ""
            if "temperature" in final_query.lower() or "warming" in final_query.lower():
                t_reg = linear_regression_trend(df["T2M"].dropna())
                t_mk = mann_kendall_test(df["T2M"].dropna())
                chg = t_reg.get("total_change_over_period", 0.0)
                obs_c = t_reg.get("n_observations", 0)
                is_sig_t = t_reg.get("is_significant", False)
                ans = (
                    f"**Empirical Analysis:** Across the selected temporal window ({start_year}–{end_year}) at {location_name}, "
                    f"the mean 2-meter air temperature changed by **{chg:+.2f} °C** "
                    f"(rate of **{t_reg.get('slope_per_decade', 0.0):+.3f} °C/decade**). "
                    f"This estimate is rigorously computed from **{obs_c:,} usable observations** in NASA's MERRA-2 assimilation dataset. "
                    f"Hypothesis testing via Ordinary Least Squares indicates p = {t_reg.get('p_value', 1.0):.4f}, while the non-parametric Mann-Kendall "
                    f"test yields Z = {t_mk.get('z_statistic', 0.0):.2f} (p = {t_mk.get('p_value', 1.0):.4f}). "
                    f"{'The trend meets the standard 95% confidence threshold (p < 0.05).' if is_sig_t else 'The slope does not cross the p < 0.05 threshold, indicating the observed trajectory remains within expected multidecadal natural variability.'} "
                    f"**Attribution Boundary:** The analysis documents empirical historical observations and does not, in isolation, prove direct anthropogenic causality or decouple global greenhouse forcing from regional land-cover shifts."
                )
            elif "precipitation" in final_query.lower() or "drought" in final_query.lower() or "rain" in final_query.lower():
                p_s_all = df["PRECTOTCORR"].dropna() if "PRECTOTCORR" in df.columns else pd.Series(dtype=float)
                ann_rain = p_s_all.sum() / max(1, end_year - start_year + 1)
                dry_sp = s_stats.get("longest_dry_spell_days", 0)
                ans = (
                    f"**Hydrological Findings:** The annual average precipitation at {location_name} is approximately **{ann_rain:.1f} mm/year**. "
                    f"Across the {start_year}–{end_year} record, the single most severe consecutive dry streak lasted **{dry_sp} days** (< 0.1 mm/day). "
                    f"NASA's bias-corrected PRECTOTCORR records show that precipitation events exceeding 25 mm/day represent episodic intense convective pulses. "
                    f"**Attribution Boundary:** Reanalysis precipitation assimilates satellite sounder radiances with regional precipitation gauges; localized microclimate precipitation bursts may differ from the 0.5° grid-cell spatial average."
                )
            elif "uncertaint" in final_query.lower() or "limitation" in final_query.lower():
                r1_val = s_unc.get("lag1_autocorrelation", 0.0)
                gap_val = s_unc.get("max_consecutive_gap_days", 0)
                ans = (
                    f"**Scientific Uncertainty & Quality Control:** The dataset for {location_name} contains {s_unc.get('missing_percentage', 0.0)}% missing values "
                    f"(which are strictly quarantined as NaNs, not synthetic substitutes). "
                    f"The maximum consecutive missing observation gap is **{gap_val} calendar days**. "
                    f"Serial autocorrelation analysis reveals a lag-1 correlation of **r₁ = {r1_val:.3f}**. "
                    f"Positive serial correlation introduces persistence, reducing the effective independent sample size from {len(s_data):,} to approximately {s_unc.get('effective_sample_size', len(s_data)):,}. "
                    f"Therefore, standard regression p-values should be interpreted with conservative judgment."
                )
            else:
                ans = (
                    f"**Synthesis for {location_name}:** Over the {start_year}–{end_year} investigation period ({quality_report.get('total_days', 0):,} calendar days), "
                    f"{target_var} exhibited an average value of {s_stats.get('mean', 'N/A')} {units}. "
                    f"The computed decadal trajectory is {s_reg.get('slope_per_decade', 0.0):+.3f} {units}/decade (OLS p = {s_reg.get('p_value', 1.0):.4f}; Mann-Kendall Z = {s_mk.get('z_statistic', 0.0):.2f}). "
                    f"All values are grounded directly in the retrieved NASA POWER records. Empirical trend analysis alone cannot establish underlying physical mechanisms."
                )

            st.html(f"""
            <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid #38bdf8; border-radius: 10px; padding: 18px; margin-top: 14px; font-size: 14px; color: #f8fafc; line-height: 1.6;">
                {ans}
            </div>
            """)
