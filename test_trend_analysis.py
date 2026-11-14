"""
Unit Tests for Advanced Trend Analysis (OLS, Mann-Kendall, Sen's Slope, Two-Period Comparison)
"""

import pytest
import pandas as pd
import numpy as np

from earthscope.analysis.trend_analysis import (
    linear_regression_trend,
    mann_kendall_test,
    compare_two_periods
)


def test_linear_regression_trend_known_slope():
    # Construct a synthetic linear series: y = 0.5 * year + 10
    years = np.arange(2000, 2025)
    dates = [pd.Timestamp(year=y, month=6, day=1) for y in years]
    y_vals = 0.5 * (years - 2000) + 10.0

    s = pd.Series(y_vals, index=dates)
    res = linear_regression_trend(s, temporal_unit="year")

    assert res["status"] == "success"
    assert res["is_significant"] is True
    assert res["direction"] == "increasing"
    assert abs(res["r_squared"] - 1.0) < 1e-3
    assert abs(res["slope"] - 0.5) < 1e-2
    assert res["p_value"] < 0.001


def test_mann_kendall_and_sens_slope():
    # Strictly increasing series: MK Z should be strongly positive and p < 0.05
    y_inc = np.linspace(10, 50, 30)
    s_inc = pd.Series(y_inc)
    res_inc = mann_kendall_test(s_inc)

    assert res_inc["status"] == "success"
    assert res_inc["trend"] == "increasing"
    assert res_inc["is_significant"] is True
    assert res_inc["z_statistic"] > 3.0
    assert res_inc["p_value"] < 0.05
    assert res_inc["sens_slope"] > 0

    # Stationary oscillating series: should have no monotonic trend (p >> 0.05)
    y_flat = [20.0, 22.0, 19.0, 21.0, 20.0] * 6
    s_flat = pd.Series(y_flat)
    res_flat = mann_kendall_test(s_flat)

    assert res_flat["status"] == "success"
    assert res_flat["is_significant"] is False
    assert res_flat["trend"] == "no_trend"
    assert res_flat["p_value"] > 0.5


def test_sens_slope_outlier_robustness():
    # Linear series with one extreme isolated outlier
    x = np.arange(25, dtype=float)
    y = 1.0 * x
    # Inject massive spike outlier at index 12
    y[12] = 500.0

    s = pd.Series(y)
    res_mk = mann_kendall_test(s)

    # Sen's median slope should still be very close to 1.0 despite the massive outlier
    assert abs(res_mk["sens_slope"] - 1.0) < 0.15


def test_compare_two_periods():
    dates = pd.date_range("2015-01-01", "2024-12-31", freq="D")
    # Period A: 2015-2019 mean = 20.0
    # Period B: 2020-2024 mean = 25.0
    np.random.seed(123)
    vals = []
    for d in dates:
        if d.year <= 2019:
            vals.append(20.0 + np.random.normal(0, 1.0))
        else:
            vals.append(25.0 + np.random.normal(0, 1.0))

    s = pd.Series(vals, index=dates)
    comp = compare_two_periods(s, period_a_years=(2015, 2019), period_b_years=(2020, 2024), var_name="T2M")

    assert comp["status"] == "success"
    assert comp["is_significant"] is True
    assert abs(comp["mean_a"] - 20.0) < 0.2
    assert abs(comp["mean_b"] - 25.0) < 0.2
    assert abs(comp["delta"] - 5.0) < 0.3
    assert comp["p_value"] < 0.001
    assert comp["cohens_d"] > 2.0  # Large effect size
