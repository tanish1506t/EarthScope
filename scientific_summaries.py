"""
Evidence-Grounded Scientific Summaries and Insights
Generates strictly factual, reproducible scientific conclusions grounded in calculated statistics.
Never hallucinates numbers; strictly adheres to NASA Space Apps Challenge standards.
"""

import os
from typing import Dict, Any, Optional, List
import pandas as pd

from earthscope.config import PARAMETERS_META


def generate_trend_insight(
    var_name: str,
    location_name: str,
    lat: float,
    lon: float,
    start_year: int,
    end_year: int,
    stats_dict: Dict[str, Any],
    trend_dict: Dict[str, Any],
    mk_dict: Dict[str, Any],
    uncertainty_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Constructs an evidence-grounded scientific summary for a single variable over a specified time window.
    Strictly uses actual calculated numbers X, Y, p-values, and confidence intervals.
    """
    meta = PARAMETERS_META.get(var_name, {})
    units = meta.get("units", "")
    readable_name = meta.get("name", var_name)
    n_obs = stats_dict.get("valid_observations", 0)
    total_recs = stats_dict.get("total_records", 0)
    missing_pct = stats_dict.get("missing_pct", 0.0)

    # If insufficient data
    if n_obs < 15 or trend_dict.get("status") != "success":
        return {
            "title": f"Observational Summary: {readable_name} ({location_name})",
            "verdict": "Insufficient Data for Conclusive Trend Attribution",
            "summary_text": (
                f"For {location_name} ({lat:.2f}°, {lon:.2f}°) over the period {start_year}–{end_year}, "
                f"only {n_obs} valid observations were retrieved out of {total_recs} possible days ({missing_pct}% missing). "
                f"Statistical guidelines require a higher density of continuous observations to establish reliable climate trends."
            ),
            "key_metrics": {},
            "scientific_disclaimer": "Insufficient data records prevent robust hypothesis testing."
        }

    slope = trend_dict.get("slope", 0.0)
    slope_dec = trend_dict.get("slope_per_decade", 0.0)
    total_change = trend_dict.get("total_change_over_period", 0.0)
    p_val = trend_dict.get("p_value", 1.0)
    r2 = trend_dict.get("r_squared", 0.0)
    ci_lower = trend_dict.get("ci_slope_lower", 0.0)
    ci_upper = trend_dict.get("ci_slope_upper", 0.0)
    is_sig = trend_dict.get("is_significant", False)
    direction = trend_dict.get("direction", "flat")

    mk_trend = mk_dict.get("trend", "no_trend")
    mk_z = mk_dict.get("z_statistic", 0.0)
    mk_p = mk_dict.get("p_value", 1.0)
    sens_slope = mk_dict.get("sens_slope", 0.0)

    mean_val = stats_dict.get("mean", 0.0)
    min_val = stats_dict.get("min", 0.0)
    max_val = stats_dict.get("max", 0.0)
    min_date = stats_dict.get("min_date", "")
    max_date = stats_dict.get("max_date", "")

    # Format direction descriptions
    if "temperature" in meta.get("category", "") or var_name in ("T2M", "T2M_MAX", "T2M_MIN", "TS"):
        shift_word = "warming" if slope > 0 else "cooling"
    elif var_name == "PRECTOTCORR":
        shift_word = "wetting" if slope > 0 else "drying"
    else:
        shift_word = "increasing" if slope > 0 else "decreasing"

    # Core scientific statement adhering to prompt template:
    # "Across the selected period, the annual mean temperature increased by X °C. This estimate is based on Y usable observations..."
    if is_sig:
        significance_statement = (
            f"The change is statistically significant at the 95% confidence level (OLS p = {p_val:.4f}, R² = {r2:.3f}; "
            f"Mann-Kendall Z = {mk_z:.2f}, p = {mk_p:.4f})."
        )
        verdict = f"Statistically Significant {shift_word.capitalize()} Trend"
    else:
        significance_statement = (
            f"However, this slope is not statistically discernible from natural climate variability at the 95% confidence level "
            f"(OLS p = {p_val:.4f} ≥ 0.05, R² = {r2:.3f}; Mann-Kendall p = {mk_p:.4f})."
        )
        verdict = "No Statistically Significant Trend (High Natural Variability)"

    change_sign = "+" if total_change > 0 else ""
    summary_paragraph = (
        f"Across the selected period ({start_year}–{end_year}), the estimated change in {readable_name.lower()} "
        f"for {location_name} ({lat:.4f}°, {lon:.4f}°) was {change_sign}{total_change:.2f} {units} "
        f"(linear rate of {change_sign}{slope_dec:.3f} {units}/decade). "
        f"This estimate is based on {n_obs:,} usable observations from the NASA POWER agroclimatological dataset "
        f"({missing_pct}% missing records across {total_recs:,} calendar days). "
        f"{significance_statement} "
        f"The non-parametric Sen's median slope was {sens_slope:.4f} {units}/step. "
        f"Over this span, the observed values averaged {mean_val:.2f} {units}, ranging from an extreme low of {min_val:.2f} {units} "
        f"(recorded on {min_date}) to a peak of {max_val:.2f} {units} (recorded on {max_date})."
    )

    autocorr_msg = uncertainty_dict.get("autocorr_assessment", "")

    scientific_disclaimer = (
        "Scientific Attribution Boundary: This statistical analysis describes empirical historical observations from NASA's satellite-derived "
        "and meteorological assimilation products. Linear trends and correlation coefficients do not, by themselves, establish direct physical causality "
        "or isolate specific anthropogenic greenhouse forcings from regional land-use changes or multidecadal natural oscillations."
    )

    return {
        "title": f"Scientific Finding: {readable_name} ({location_name})",
        "verdict": verdict,
        "summary_text": summary_paragraph,
        "autocorrelation_note": autocorr_msg,
        "scientific_disclaimer": scientific_disclaimer,
        "key_metrics": {
            "Total Estimated Change": f"{change_sign}{total_change:.2f} {units}",
            "Decadal Rate": f"{change_sign}{slope_dec:.3f} {units}/decade",
            "OLS p-value": f"{p_val:.4f}",
            "Mann-Kendall Z": f"{mk_z:.2f}",
            "Usable Observations": f"{n_obs:,}",
            "Historical Average": f"{mean_val:.2f} {units}",
            "Extreme Minimum": f"{min_val:.2f} {units} ({min_date})",
            "Extreme Maximum": f"{max_val:.2f} {units} ({max_date})"
        }
    }


def generate_period_comparison_insight(comp_dict: Dict[str, Any], location_name: str) -> Dict[str, Any]:
    """
    Constructs an evidence-grounded summary comparing two time periods.
    """
    if comp_dict.get("status") != "success":
        return {
            "title": "Period Comparison",
            "summary_text": comp_dict.get("message", "Insufficient observations for period comparison.")
        }

    var_name = comp_dict["var_name"]
    meta = PARAMETERS_META.get(var_name, {})
    units = comp_dict["units"]
    label_a = comp_dict["period_a_label"]
    label_b = comp_dict["period_b_label"]
    m_a = comp_dict["mean_a"]
    m_b = comp_dict["mean_b"]
    delta = comp_dict["delta"]
    pct = comp_dict["pct_change"]
    p_val = comp_dict["p_value"]
    is_sig = comp_dict["is_significant"]
    cohens_d = comp_dict["cohens_d"]

    diff_sign = "+" if delta > 0 else ""
    pct_str = f" ({diff_sign}{pct:.1f}%)" if pct is not None else ""

    if is_sig:
        sig_text = (
            f"A two-sample Welch's t-test indicates this difference is statistically significant "
            f"(t = {comp_dict['t_statistic']:.2f}, p = {p_val:.4f} < 0.05), with an effect size of Cohen's d = {cohens_d:.2f}."
        )
    else:
        sig_text = (
            f"A two-sample Welch's t-test indicates this shift is not statistically significant "
            f"(t = {comp_dict['t_statistic']:.2f}, p = {p_val:.4f} ≥ 0.05), suggesting observed variations are within expected sampling noise."
        )

    text = (
        f"Comparing the baseline period ({label_a}) against the recent period ({label_b}) in {location_name}: "
        f"The mean {meta.get('name', var_name).lower()} shifted from {m_a:.2f} {units} to {m_b:.2f} {units}, "
        f"representing a net departure of {diff_sign}{delta:.2f} {units}{pct_str}. "
        f"{sig_text}"
    )

    return {
        "title": f"Comparative Period Analysis: {label_a} vs {label_b}",
        "summary_text": text,
        "delta": f"{diff_sign}{delta:.2f} {units}",
        "p_value": f"{p_val:.4f}",
        "is_significant": is_sig
    }
