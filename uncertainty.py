"""
Scientific Uncertainty and Autocorrelation Analysis
Quantifies observation completeness, missing data risk, lag-1 autocorrelation,
and effective sample size (N_eff) adjustments for climate time series.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from scipy import stats


def evaluate_series_uncertainty(series: pd.Series, var_name: str) -> Dict[str, Any]:
    """
    Evaluates observational completeness, max consecutive missing gaps,
    lag-1 autocorrelation (r_1), and effective sample size (N_eff).
    """
    total_n = len(series)
    valid_s = series.dropna()
    valid_n = len(valid_s)
    missing_n = total_n - valid_n
    missing_pct = round((missing_n / total_n * 100.0), 2) if total_n > 0 else 0.0

    # Consecutive missing gaps
    is_missing = series.isna()
    max_gap = 0
    cur_gap = 0
    for m in is_missing:
        if m:
            cur_gap += 1
            if cur_gap > max_gap:
                max_gap = cur_gap
        else:
            cur_gap = 0

    # Completeness risk flag
    if missing_pct <= 5.0:
        completeness_rating = "High Completeness (≥95%)"
        risk_level = "Low"
    elif missing_pct <= 15.0:
        completeness_rating = "Moderate Completeness (85–95%)"
        risk_level = "Moderate"
    elif missing_pct <= 30.0:
        completeness_rating = "Elevated Missingness (70–85%)"
        risk_level = "Caution: Trend estimates have elevated variance"
    else:
        completeness_rating = "Substantial Missingness (<70%)"
        risk_level = "High: Insufficient continuous data for definitive claims"

    # Autocorrelation (lag-1)
    if valid_n > 10:
        s_vals = valid_s.values.astype(float)
        # Compute Pearson r between s[t] and s[t-1]
        r1 = float(np.corrcoef(s_vals[:-1], s_vals[1:])[0, 1])
        if np.isnan(r1):
            r1 = 0.0
    else:
        r1 = 0.0

    # Effective sample size (N_eff) adjustment for positive autocorrelation
    # N_eff = N * (1 - r1) / (1 + r1)
    if 0.0 < r1 < 0.95:
        n_eff = int(valid_n * (1.0 - r1) / (1.0 + r1))
        n_eff = max(3, n_eff)
    else:
        n_eff = valid_n

    autocorr_impact = ""
    if r1 >= 0.5:
        autocorr_impact = f"Strong persistence (r₁ = {r1:.2f}). Ordinary linear regression significantly overstates statistical significance; effective sample size reduced from {valid_n} to {n_eff}."
    elif r1 >= 0.2:
        autocorr_impact = f"Moderate persistence (r₁ = {r1:.2f}). Slight variance inflation in trend slope."
    else:
        autocorr_impact = f"Low serial correlation (r₁ = {r1:.2f}). Standard parametric assumptions are reasonable."

    return {
        "variable": var_name,
        "total_records": total_n,
        "valid_observations": valid_n,
        "missing_records": missing_n,
        "missing_percentage": missing_pct,
        "max_consecutive_gap_days": max_gap,
        "completeness_rating": completeness_rating,
        "uncertainty_risk": risk_level,
        "lag1_autocorrelation": round(r1, 3),
        "effective_sample_size": n_eff,
        "autocorr_assessment": autocorr_impact
    }
