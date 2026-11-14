"""
Data Cleaning and Quality Control
Transforms raw NASA POWER responses into sanitized, validated pandas DataFrames.
"""

import logging
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

from earthscope.config import PARAMETERS_META, NASA_FILL_VALUE

logger = logging.getLogger(__name__)


def get_meteorological_season(month: int, latitude: float = 0.0) -> str:
    """
    Returns meteorological season based on month and hemisphere.
    For Northern Hemisphere:
      DJF = Winter, MAM = Spring, JJA = Summer, SON = Autumn
    For Southern Hemisphere:
      DJF = Summer, MAM = Autumn, JJA = Winter, SON = Spring
    For Tropical latitudes (-10 <= lat <= 10):
      Optionally referred to as Dry/Wet, but labeled clearly.
    """
    if latitude >= 0:
        if month in (12, 1, 2):
            return "Winter"
        elif month in (3, 4, 5):
            return "Spring"
        elif month in (6, 7, 8):
            return "Summer"
        else:
            return "Autumn"
    else:
        if month in (12, 1, 2):
            return "Summer"
        elif month in (3, 4, 5):
            return "Autumn"
        elif month in (6, 7, 8):
            return "Winter"
        else:
            return "Spring"


def parse_and_clean_nasa_data(raw_payload: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Parses NASA POWER API response into a clean, typed DataFrame.
    
    Returns:
    - df: DataFrame indexed by datetime with sanitized numerical columns
    - quality_report: Dict detailing valid observation counts, missing percentages, and bounds checks.
    """
    if "properties" not in raw_payload or "parameter" not in raw_payload["properties"]:
        raise ValueError("Invalid payload: Missing 'properties.parameter' in NASA POWER response.")

    param_dict = raw_payload["properties"]["parameter"]
    meta = raw_payload.get("_retrieval_metadata", {})
    lat = meta.get("latitude", 0.0)

    # Collect all dates across all parameters
    all_dates = set()
    for p_name, p_data in param_dict.items():
        if isinstance(p_data, dict):
            all_dates.update(p_data.keys())

    if not all_dates:
        raise ValueError("No temporal records found in NASA POWER response.")

    sorted_dates = sorted(list(all_dates))
    records = []
    for d_str in sorted_dates:
        row = {"date_str": d_str}
        for p_name, p_data in param_dict.items():
            val = p_data.get(d_str, None)
            row[p_name] = val
        records.append(row)

    df = pd.DataFrame(records)
    
    # Parse dates
    df["date"] = pd.to_datetime(df["date_str"], format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["date"]).set_index("date")
    df = df.sort_index()

    # Drop duplicate dates if any
    if df.index.duplicated().any():
        df = df[~df.index.duplicated(keep="first")]

    total_records = len(df)
    quality_report: Dict[str, Any] = {
        "total_days": total_records,
        "date_start": df.index.min().strftime("%Y-%m-%d") if total_records > 0 else None,
        "date_end": df.index.max().strftime("%Y-%m-%d") if total_records > 0 else None,
        "variables": {}
    }

    # Clean and sanitize each variable
    for col in df.columns:
        if col == "date_str":
            continue
        
        # Coerce to numeric
        df[col] = pd.to_numeric(df[col], errors="coerce")

        # Replace NASA fill values (-999, -999.0)
        df[col] = df[col].apply(lambda v: np.nan if (v == NASA_FILL_VALUE or v <= -900.0) else v)

        # Special precipitation handling: zero-out tiny floating point negative artifacts (-0.05 to 0) before bounds check
        if col == "PRECTOTCORR":
            df[col] = df[col].apply(lambda v: 0.0 if (not np.isnan(v) and -0.05 <= v < 0.0) else v)

        # Apply physical boundary filtering if metadata exists
        meta_info = PARAMETERS_META.get(col, {})
        min_v = meta_info.get("min_valid", -np.inf)
        max_v = meta_info.get("max_valid", np.inf)

        # Count out of bounds
        out_of_bounds = ((df[col] < min_v) | (df[col] > max_v)) & df[col].notna()
        oob_count = int(out_of_bounds.sum())

        if oob_count > 0:
            logger.warning(f"Variable {col} has {oob_count} values outside physical range [{min_v}, {max_v}]. Masking as NaN.")
            df.loc[out_of_bounds, col] = np.nan

        valid_count = int(df[col].notna().sum())
        missing_count = total_records - valid_count
        missing_pct = round((missing_count / total_records * 100.0), 2) if total_records > 0 else 0.0

        quality_report["variables"][col] = {
            "name": meta_info.get("name", col),
            "units": meta_info.get("units", ""),
            "valid_observations": valid_count,
            "missing_observations": missing_count,
            "missing_percentage": missing_pct,
            "out_of_bounds_masked": oob_count,
            "min_observed": float(df[col].min()) if valid_count > 0 else None,
            "max_observed": float(df[col].max()) if valid_count > 0 else None,
            "mean_observed": float(df[col].mean()) if valid_count > 0 else None
        }

    # Add temporal calendar helper columns
    df["year"] = df.index.year
    df["month"] = df.index.month
    df["day"] = df.index.day
    df["day_of_year"] = df.index.dayofyear
    df["season"] = [get_meteorological_season(m, lat) for m in df["month"]]

    if "date_str" in df.columns:
        df = df.drop(columns=["date_str"])

    return df, quality_report
