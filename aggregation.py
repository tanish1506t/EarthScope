"""
Data Aggregation Module
Performs scientifically sound temporal aggregations: Daily -> Monthly -> Annual,
with strict missing-data thresholds, climatological baselines, and anomalies.
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np

from earthscope.config import PARAMETERS_META, MIN_MONTH_DAYS_THRESHOLD

logger = logging.getLogger(__name__)


def aggregate_monthly(df: pd.DataFrame, min_valid_days: int = MIN_MONTH_DAYS_THRESHOLD) -> pd.DataFrame:
    """
    Aggregates daily observations into monthly summaries.
    
    Rules:
    - Mean for intensive state variables (Temperature, Radiation, Soil Moisture).
    - Sum for extensive accumulated flux variables (Precipitation).
    - Threshold enforcement: If valid daily observations < min_valid_days in a month,
      the aggregate is set to NaN to prevent misleading skew.
    - If valid days >= min_valid_days, precipitation is scaled by (days_in_month / valid_days)
      to adjust for any small missing slice.
    """
    if df.empty:
        return pd.DataFrame()

    # Work on a copy with Year-Month period
    temp_df = df.copy()
    if not isinstance(temp_df.index, pd.DatetimeIndex):
        temp_df.index = pd.to_datetime(temp_df.index)

    temp_df["year_month"] = temp_df.index.to_period("M")
    grouped = temp_df.groupby("year_month")

    records = []
    for ym, group in grouped:
        days_in_month = ym.days_in_month
        row: Dict[str, Any] = {
            "date": ym.to_timestamp(),
            "year": ym.year,
            "month": ym.month,
            "days_in_month": days_in_month,
        }

        for col in df.columns:
            if col in ("year", "month", "day", "day_of_year", "season", "year_month"):
                continue

            series = group[col].dropna()
            valid_count = len(series)
            row[f"{col}_count"] = valid_count

            if valid_count < min_valid_days:
                row[col] = np.nan
            else:
                meta = PARAMETERS_META.get(col, {})
                agg_type = meta.get("agg_method", "mean")

                if agg_type == "sum" or col == "PRECTOTCORR":
                    raw_sum = series.sum()
                    # Normalized monthly sum accounting for missing days
                    adjusted_sum = raw_sum * (days_in_month / valid_count)
                    row[col] = round(adjusted_sum, 2)
                else:
                    row[col] = round(float(series.mean()), 3)

        records.append(row)

    monthly_df = pd.DataFrame(records).set_index("date").sort_index()
    return monthly_df


def aggregate_annual(monthly_df: pd.DataFrame, min_valid_months: int = 10) -> pd.DataFrame:
    """
    Aggregates monthly data to annual summaries.
    Requires at least `min_valid_months` (default 10) per year to avoid seasonality bias.
    """
    if monthly_df.empty:
        return pd.DataFrame()

    temp_df = monthly_df.copy()
    temp_df["year"] = temp_df.index.year
    grouped = temp_df.groupby("year")

    records = []
    for year, group in grouped:
        row: Dict[str, Any] = {
            "year": year,
            "date": pd.Timestamp(year=year, month=7, day=1),  # Mid-year reference
            "valid_months": len(group)
        }

        for col in monthly_df.columns:
            if col in ("year", "month", "days_in_month", "date") or col.endswith("_count"):
                continue

            series = group[col].dropna()
            valid_m = len(series)

            if valid_m < min_valid_months:
                row[col] = np.nan
            else:
                meta = PARAMETERS_META.get(col, {})
                agg_type = meta.get("agg_method", "mean")

                if agg_type == "sum" or col == "PRECTOTCORR":
                    # Scale annual total if 10 or 11 months are present
                    row[col] = round(float(series.sum() * (12.0 / valid_m)), 2)
                else:
                    row[col] = round(float(series.mean()), 3)

        records.append(row)

    annual_df = pd.DataFrame(records).set_index("year").sort_index()
    return annual_df


def calculate_climatology(monthly_df: pd.DataFrame, baseline_start: Optional[int] = None, baseline_end: Optional[int] = None) -> pd.DataFrame:
    """
    Calculates multi-year average (climatological normal) for each calendar month (1 to 12).
    Optionally subsets to baseline period (e.g., 2015-2020).
    """
    if monthly_df.empty:
        return pd.DataFrame()

    m_df = monthly_df.copy()
    if baseline_start is not None and baseline_end is not None:
        m_df = m_df[(m_df.index.year >= baseline_start) & (m_df.index.year <= baseline_end)]

    numeric_cols = [c for c in m_df.columns if c in PARAMETERS_META]
    clim_mean = m_df.groupby("month")[numeric_cols].mean()
    clim_std = m_df.groupby("month")[numeric_cols].std()

    clim_summary = clim_mean.copy()
    for c in numeric_cols:
        clim_summary[f"{c}_std"] = clim_std[c]

    return clim_summary


def calculate_anomalies(monthly_df: pd.DataFrame, climatology: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates monthly anomalies relative to the climatological monthly averages.
    Anomaly = Monthly_Value - Climatology_Mean_for_Month
    """
    if monthly_df.empty or climatology.empty:
        return pd.DataFrame()

    anomaly_df = monthly_df.copy()
    numeric_cols = [c for c in monthly_df.columns if c in PARAMETERS_META]

    for col in numeric_cols:
        if col in climatology.columns:
            month_to_baseline = climatology[col].to_dict()
            baseline_series = anomaly_df["month"].map(month_to_baseline)
            anomaly_df[f"{col}_anomaly"] = anomaly_df[col] - baseline_series

    return anomaly_df


def compute_rolling_averages(daily_df: pd.DataFrame, var_name: str, windows: List[int] = [7, 30, 90, 365]) -> pd.DataFrame:
    """
    Computes trailing rolling averages for smoothing high-frequency noise.
    """
    res_df = pd.DataFrame(index=daily_df.index)
    res_df[var_name] = daily_df[var_name]
    
    for w in windows:
        if len(daily_df) >= w:
            res_df[f"{var_name}_roll_{w}d"] = daily_df[var_name].rolling(window=w, min_periods=max(1, w // 2)).mean()
            
    return res_df
