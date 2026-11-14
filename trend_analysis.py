"""
Advanced Trend Analysis Module
Implements OLS regression with confidence bands, non-parametric Mann-Kendall test,
Sen's slope estimator, and period-to-period comparative diagnostics.
"""

from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
from scipy import stats

from earthscope.config import PARAMETERS_META, SIGNIFICANCE_ALPHA, MIN_OBSERVATIONS_FOR_TREND


def linear_regression_trend(
    series: pd.Series,
    temporal_unit: str = "year",
    alpha: float = SIGNIFICANCE_ALPHA
) -> Dict[str, Any]:
    """
    Fits Ordinary Least Squares (OLS) linear regression over time.
    
    temporal_unit: 'year' (default, slope scaled to units/year and units/decade)
                   'day' (slope per day)
                   'month' (slope per month)
    """
    clean_s = series.dropna()
    n = len(clean_s)

    if n < 5:
        return {
            "status": "insufficient_data",
            "message": f"Requires at least 5 observations for linear regression. Received: {n}",
            "n_observations": n
        }

    # Convert timestamps to fractional years or sequential index
    if isinstance(clean_s.index, pd.DatetimeIndex):
        # Convert to fractional year for clean annual/decadal interpretation
        start_ts = clean_s.index[0]
        x_days = (clean_s.index - start_ts).total_seconds() / 86400.0
        x_years = x_days / 365.25
        x = x_years.values
        x_label = "years"
    elif isinstance(clean_s.index, pd.PeriodIndex):
        x = np.arange(n, dtype=float)
        x_label = "periods"
    else:
        # Numeric index (e.g. year integers)
        x = np.array(clean_s.index, dtype=float)
        x_label = "units"

    y = clean_s.values.astype(float)

    # Perform linear regression
    slope, intercept, r_val, p_val, std_err = stats.linregress(x, y)
    r_squared = float(r_val ** 2)

    # Degrees of freedom and t-critical for (1 - alpha) confidence interval
    df = n - 2
    t_crit = stats.t.ppf(1.0 - alpha / 2.0, df)
    ci_slope_lower = slope - t_crit * std_err
    ci_slope_upper = slope + t_crit * std_err

    # Compute fitted values and residuals
    y_pred = intercept + slope * x
    residuals = y - y_pred
    s_err = np.sqrt(np.sum(residuals ** 2) / max(1, df))

    # Standard error of prediction bands along x
    x_mean = np.mean(x)
    ss_x = np.sum((x - x_mean) ** 2)
    with np.errstate(divide='ignore', invalid='ignore'):
        ci_band = t_crit * s_err * np.sqrt(1.0 / n + (x - x_mean) ** 2 / (ss_x if ss_x > 0 else 1.0))

    # Interpret slope in annual and decadal terms
    slope_per_decade = slope * 10.0 if x_label == "years" or temporal_unit == "year" else slope * 10.0
    total_change = slope * (x[-1] - x[0]) if len(x) > 1 else 0.0

    is_significant = bool(p_val < alpha)
    direction = "increasing" if slope > 0 else ("decreasing" if slope < 0 else "flat")
    if not is_significant:
        significance_label = "No statistically significant trend (p ≥ 0.05)"
    else:
        significance_label = f"Statistically significant {direction} trend (p < 0.05)"

    return {
        "status": "success",
        "n_observations": n,
        "slope": round(float(slope), 5),
        "slope_per_decade": round(float(slope_per_decade), 4),
        "intercept": round(float(intercept), 4),
        "r_squared": round(float(r_squared), 4),
        "r_value": round(float(r_val), 4),
        "p_value": float(p_val),
        "std_error": round(float(std_err), 5),
        "ci_slope_95": (round(float(ci_slope_lower), 5), round(float(ci_slope_upper), 5)),
        "ci_slope_lower": round(float(ci_slope_lower), 5),
        "ci_slope_upper": round(float(ci_slope_upper), 5),
        "total_change_over_period": round(float(total_change), 3),
        "is_significant": is_significant,
        "direction": direction,
        "significance_label": significance_label,
        "x_values": x.tolist(),
        "y_actual": y.tolist(),
        "y_fitted": y_pred.tolist(),
        "ci_lower_band": (y_pred - ci_band).tolist(),
        "ci_upper_band": (y_pred + ci_band).tolist()
    }


def mann_kendall_test(series: pd.Series, alpha: float = SIGNIFICANCE_ALPHA) -> Dict[str, Any]:
    """
    Performs the non-parametric Mann-Kendall Trend Test.
    Robust to non-normality and missing distributions.
    """
    clean_s = series.dropna()
    n = len(clean_s)

    if n < 10:
        return {
            "status": "insufficient_data",
            "message": f"Mann-Kendall test requires at least 10 observations. Received: {n}",
            "n_observations": n
        }

    x = clean_s.values.astype(float)
    
    # Compute Kendall's S
    # S = sum(sgn(x_j - x_k)) for k < j
    # np.triu_indices(n, k=1) gives row_idx, col_idx where col_idx > row_idx
    row_idx, col_idx = np.triu_indices(n, k=1)
    pair_diffs = x[col_idx] - x[row_idx]
    s = np.sum(np.sign(pair_diffs))

    # Account for tied groups in variance calculation
    unique_vals, counts = np.unique(x, return_counts=True)
    tied_sum = np.sum(counts * (counts - 1) * (2 * counts + 5))

    var_s = (n * (n - 1) * (2 * n + 5) - tied_sum) / 18.0

    if var_s <= 0:
        z = 0.0
        p_val = 1.0
    else:
        if s > 0:
            z = (s - 1) / np.sqrt(var_s)
        elif s < 0:
            z = (s + 1) / np.sqrt(var_s)
        else:
            z = 0.0
        # Two-tailed test
        p_val = 2.0 * (1.0 - stats.norm.cdf(abs(z)))

    # Compute Sen's slope (median of all pairwise slopes)
    # pair_diffs is x[col] - x[row], where col > row
    time_diffs = (col_idx - row_idx).astype(float)
    pairwise_slopes = pair_diffs / time_diffs
    sens_slope = float(np.median(pairwise_slopes))

    is_significant = bool(p_val < alpha)
    if is_significant:
        trend = "increasing" if z > 0 else "decreasing"
    else:
        trend = "no_trend"

    return {
        "status": "success",
        "n_observations": n,
        "s_statistic": int(s),
        "z_statistic": round(float(z), 4),
        "p_value": float(p_val),
        "sens_slope": round(sens_slope, 5),
        "is_significant": is_significant,
        "trend": trend,
        "verdict": (
            f"Statistically significant {trend} trend (Z = {z:.2f}, p = {p_val:.4f})"
            if is_significant
            else f"No statistically significant trend detected (Z = {z:.2f}, p = {p_val:.4f})"
        )
    }


def compare_two_periods(
    series: pd.Series,
    period_a_years: Tuple[int, int],
    period_b_years: Tuple[int, int],
    var_name: str
) -> Dict[str, Any]:
    """
    Compares two temporal windows (e.g. 2015-2019 vs 2020-2024).
    Calculates differences, percentage change, Welch's t-test, and effect size.
    """
    if not isinstance(series.index, pd.DatetimeIndex):
        raise ValueError("Series index must be a DatetimeIndex for period comparisons.")

    s_a = series[(series.index.year >= period_a_years[0]) & (series.index.year <= period_a_years[1])].dropna()
    s_b = series[(series.index.year >= period_b_years[0]) & (series.index.year <= period_b_years[1])].dropna()

    n_a = len(s_a)
    n_b = len(s_b)

    meta = PARAMETERS_META.get(var_name, {})
    units = meta.get("units", "")

    if n_a < 3 or n_b < 3:
        return {
            "status": "insufficient_data",
            "message": f"Each period requires at least 3 records. Period A has {n_a}, Period B has {n_b}."
        }

    mean_a = float(s_a.mean())
    mean_b = float(s_b.mean())
    std_a = float(s_a.std(ddof=1)) if n_a > 1 else 0.0
    std_b = float(s_b.std(ddof=1)) if n_b > 1 else 0.0

    delta = mean_b - mean_a
    pct_change = (delta / abs(mean_a) * 100.0) if abs(mean_a) > 1e-4 else None

    # Welch's t-test (unequal variances assumed)
    t_stat, p_val = stats.ttest_ind(s_b, s_a, equal_var=False)

    # Cohen's d effect size
    pooled_std = np.sqrt(((n_a - 1) * (std_a ** 2) + (n_b - 1) * (std_b ** 2)) / (n_a + n_b - 2))
    cohens_d = float(delta / pooled_std) if pooled_std > 1e-6 else 0.0

    return {
        "status": "success",
        "var_name": var_name,
        "units": units,
        "period_a_label": f"{period_a_years[0]}–{period_a_years[1]}",
        "period_b_label": f"{period_b_years[0]}–{period_b_years[1]}",
        "n_a": n_a,
        "n_b": n_b,
        "mean_a": round(mean_a, 3),
        "mean_b": round(mean_b, 3),
        "std_a": round(std_a, 3),
        "std_b": round(std_b, 3),
        "delta": round(delta, 3),
        "pct_change": round(pct_change, 2) if pct_change is not None else None,
        "t_statistic": round(float(t_stat), 3),
        "p_value": float(p_val),
        "cohens_d": round(cohens_d, 3),
        "is_significant": bool(p_val < SIGNIFICANCE_ALPHA)
    }
