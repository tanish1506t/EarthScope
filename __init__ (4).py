"""
Scientific Analysis Module for EarthScope
"""
from earthscope.analysis.descriptive_stats import compute_descriptive_stats
from earthscope.analysis.trend_analysis import (
    linear_regression_trend,
    mann_kendall_test,
    compare_two_periods
)
from earthscope.analysis.uncertainty import evaluate_series_uncertainty

__all__ = [
    "compute_descriptive_stats",
    "linear_regression_trend",
    "mann_kendall_test",
    "compare_two_periods",
    "evaluate_series_uncertainty"
]
