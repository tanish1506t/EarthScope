"""
Unit Tests for Uncertainty, Gap Analysis, and Autocorrelation
"""

import pytest
import pandas as pd
import numpy as np

from earthscope.analysis.uncertainty import evaluate_series_uncertainty


def test_uncertainty_and_gaps():
    # 100 days series with 10 missing values in a single continuous gap
    vals = [22.0] * 100
    for i in range(20, 30):
        vals[i] = np.nan

    s = pd.Series(vals)
    unc = evaluate_series_uncertainty(s, "T2M")

    assert unc["total_records"] == 100
    assert unc["valid_observations"] == 90
    assert unc["missing_records"] == 10
    assert unc["missing_percentage"] == 10.0
    assert unc["max_consecutive_gap_days"] == 10
    assert "Moderate Completeness" in unc["completeness_rating"]


def test_autocorrelation_effective_n():
    # Highly persistent AR(1) process: x[t] = 0.8 * x[t-1] + e[t]
    np.random.seed(42)
    n = 200
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = 0.8 * x[t - 1] + np.random.normal(0, 0.5)

    s = pd.Series(x)
    unc = evaluate_series_uncertainty(s, "T2M")

    # Lag-1 correlation should be positive and close to 0.8
    assert unc["lag1_autocorrelation"] > 0.5
    # Effective sample size N_eff must be significantly lower than 200
    assert unc["effective_sample_size"] < 100
    assert "Strong persistence" in unc["autocorr_assessment"]
