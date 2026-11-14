"""
Tests for Statistical Analysis and Trend Functions
"""

import pytest
import numpy as np
import pandas as pd
from backend.app.services.statistics import StatisticsService

def test_descriptive_statistics():
    data = pd.Series([10.0, 12.0, 15.0, 18.0, 20.0, np.nan, 25.0])
    stats = StatisticsService.calculate_descriptive_stats(data, "T2M")

    assert stats.total_records == 7
    assert stats.valid_observations == 6
    assert stats.min == 10.0
    assert stats.max == 25.0
    assert stats.mean == 16.67
    assert stats.median == 16.5
    assert len(stats.histogram) > 0

def test_linear_regression_trend():
    # Construct a known linear sequence: y = 20.0 + 0.5 * x
    years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
    temps = [20.0 + 0.5 * i for i in range(len(years))]
    
    rows = []
    for y, t in zip(years, temps):
        for m in range(1, 13):
            rows.append({
                "date": f"{y}-{m:02d}",
                "year": y,
                "month": m,
                "t2m": t + np.sin(m / 12 * 2 * np.pi)  # seasonal cycle around trend
            })
    df = pd.DataFrame(rows)
    
    trend = StatisticsService.calculate_trend(df, "t2m", "yearly")
    assert trend.n_observations == 10
    assert abs(trend.slope_per_year - 0.5) < 0.05
    assert trend.r_squared > 0.95
    assert trend.is_significant is True
    assert trend.direction == "warming"
    assert trend.mann_kendall_z > 2.0
