"""
Unit Tests for Data Aggregation (Daily -> Monthly -> Annual)
"""

import pytest
import pandas as pd
import numpy as np

from earthscope.data.aggregation import (
    aggregate_monthly,
    aggregate_annual,
    calculate_climatology,
    calculate_anomalies
)


def test_monthly_and_annual_aggregation():
    # Construct a 2-month daily DataFrame (Jan 31 days, Feb 28 days)
    dates = pd.date_range("2023-01-01", "2023-02-28", freq="D")
    df = pd.DataFrame(index=dates)
    
    # In Jan, 25 valid days (>= 20 threshold), Feb has 10 valid days (< 20 threshold)
    jan_t = [20.0] * 31
    for i in range(6):
        jan_t[i] = np.nan  # 25 valid days in Jan
    feb_t = [25.0] * 10 + [np.nan] * 18  # 10 valid days in Feb
    df["T2M"] = jan_t + feb_t

    # Precipitation: Jan has 2.0 mm/day on 25 valid days -> raw sum = 50.0 mm
    # Normalized monthly sum = 50.0 * (31 / 25) = 62.0 mm
    jan_p = [2.0] * 31
    for i in range(6):
        jan_p[i] = np.nan
    feb_p = [0.0] * 28
    df["PRECTOTCORR"] = jan_p + feb_p

    monthly_df = aggregate_monthly(df, min_valid_days=20)

    assert len(monthly_df) == 2

    # Jan should have mean 20.0
    jan_row = monthly_df.iloc[0]
    assert jan_row["T2M"] == 20.0
    assert jan_row["PRECTOTCORR"] == 62.0

    # Feb has only 10 valid days < 20, so T2M must be NaN
    feb_row = monthly_df.iloc[1]
    assert np.isnan(feb_row["T2M"])


def test_climatology_and_anomalies():
    # Create 3 years of monthly data for Month 1 (Jan) and Month 2 (Feb)
    dates = [
        pd.Timestamp("2021-01-01"), pd.Timestamp("2021-02-01"),
        pd.Timestamp("2022-01-01"), pd.Timestamp("2022-02-01"),
        pd.Timestamp("2023-01-01"), pd.Timestamp("2023-02-01")
    ]
    m_df = pd.DataFrame(index=dates)
    m_df["month"] = [d.month for d in dates]
    # Jan temps: 10, 12, 14 -> mean = 12.0
    # Feb temps: 20, 22, 24 -> mean = 22.0
    m_df["T2M"] = [10.0, 20.0, 12.0, 22.0, 14.0, 24.0]

    clim = calculate_climatology(m_df)
    assert clim.loc[1, "T2M"] == 12.0
    assert clim.loc[2, "T2M"] == 22.0

    anom = calculate_anomalies(m_df, clim)
    # 2021-01 anomaly: 10 - 12 = -2.0
    assert anom.loc[dates[0], "T2M_anomaly"] == -2.0
    # 2023-01 anomaly: 14 - 12 = +2.0
    assert anom.loc[dates[4], "T2M_anomaly"] == 2.0
