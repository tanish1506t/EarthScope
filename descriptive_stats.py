"""
Descriptive Statistics and Distribution Analysis
Computes rigorous summary metrics and distribution measures for climate variables.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from scipy import stats

from earthscope.config import PARAMETERS_META


def compute_descriptive_stats(series: pd.Series, var_name: str) -> Dict[str, Any]:
    """
    Computes comprehensive descriptive statistics for a pandas Series.
    """
    clean_s = series.dropna()
    total_len = len(series)
    valid_n = len(clean_s)

    meta = PARAMETERS_META.get(var_name, {})
    units = meta.get("units", "")

    if valid_n == 0:
        return {
            "variable": var_name,
            "units": units,
            "total_records": total_len,
            "valid_observations": 0,
            "missing_observations": total_len,
            "missing_pct": 100.0,
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "max": None,
            "iqr": None
        }

    q25, q50, q75 = np.percentile(clean_s, [25, 50, 75])
    p10, p90 = np.percentile(clean_s, [10, 90])
    mean_val = float(clean_s.mean())
    std_val = float(clean_s.std(ddof=1)) if valid_n > 1 else 0.0

    skew_val = float(stats.skew(clean_s)) if valid_n > 2 else 0.0
    kurt_val = float(stats.kurtosis(clean_s)) if valid_n > 3 else 0.0

    min_val = float(clean_s.min())
    max_val = float(clean_s.max())
    min_date = clean_s.idxmin().strftime("%Y-%m-%d") if hasattr(clean_s.idxmin(), "strftime") else str(clean_s.idxmin())
    max_date = clean_s.idxmax().strftime("%Y-%m-%d") if hasattr(clean_s.idxmax(), "strftime") else str(clean_s.idxmax())

    out: Dict[str, Any] = {
        "variable": var_name,
        "name": meta.get("name", var_name),
        "units": units,
        "total_records": total_len,
        "valid_observations": valid_n,
        "missing_observations": total_len - valid_n,
        "missing_pct": round((total_len - valid_n) / total_len * 100.0, 2) if total_len > 0 else 0.0,
        "mean": round(mean_val, 3),
        "median": round(float(q50), 3),
        "std": round(std_val, 3),
        "q25": round(float(q25), 3),
        "q75": round(float(q75), 3),
        "iqr": round(float(q75 - q25), 3),
        "p10": round(float(p10), 3),
        "p90": round(float(p90), 3),
        "min": round(min_val, 3),
        "max": round(max_val, 3),
        "range": round(max_val - min_val, 3),
        "min_date": min_date,
        "max_date": max_date,
        "skewness": round(skew_val, 3),
        "kurtosis": round(kurt_val, 3)
    }

    # Specialized metrics for precipitation
    if var_name == "PRECTOTCORR":
        rain_days = int((clean_s >= 0.1).sum())
        heavy_rain_days = int((clean_s >= 10.0).sum())
        very_heavy_rain_days = int((clean_s >= 25.0).sum())
        total_precip = float(clean_s.sum())

        # Longest dry spell (consecutive days < 0.1 mm)
        dry_mask = clean_s < 0.1
        longest_dry_spell = 0
        current_dry = 0
        for is_dry in dry_mask:
            if is_dry:
                current_dry += 1
                if current_dry > longest_dry_spell:
                    longest_dry_spell = current_dry
            else:
                current_dry = 0

        out.update({
            "total_precipitation": round(total_precip, 2),
            "rain_days_count": rain_days,
            "rain_days_pct": round(rain_days / valid_n * 100.0, 1),
            "heavy_rain_days": heavy_rain_days,
            "very_heavy_rain_days": very_heavy_rain_days,
            "longest_dry_spell_days": longest_dry_spell
        })

    return out
