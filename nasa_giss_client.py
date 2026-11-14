"""
NASA GISS GISTEMP v4 Client
Fetches and processes authentic global and hemispheric surface temperature anomaly datasets
directly from the NASA Goddard Institute for Space Studies (GISS).
Reference: https://data.giss.nasa.gov/gistemp/
"""

import os
import io
import logging
import hashlib
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import requests

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "giss")

GISS_URLS = {
    "global": "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv",
    "northern_hemisphere": "https://data.giss.nasa.gov/gistemp/tabledata_v4/NH.Ts+dSST.csv",
    "southern_hemisphere": "https://data.giss.nasa.gov/gistemp/tabledata_v4/SH.Ts+dSST.csv",
    "zonal": "https://data.giss.nasa.gov/gistemp/tabledata_v4/ZonAnn.Ts+dSST.csv"
}


class NASAGissClient:
    """
    Client for NASA GISTEMP v4 Surface Temperature Analysis tables.
    """

    def __init__(self, cache_enabled: bool = True, cache_dir: str = CACHE_DIR, timeout: int = 20):
        self.cache_enabled = cache_enabled
        self.cache_dir = cache_dir
        self.timeout = timeout
        if self.cache_enabled:
            os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, dataset_key: str) -> str:
        return os.path.join(self.cache_dir, f"gistemp_{dataset_key}.csv")

    def fetch_gistemp_data(self, dataset_key: str = "global", force_refresh: bool = False) -> pd.DataFrame:
        """
        Fetches and cleans NASA GISTEMP v4 dataset.
        Returns DataFrame indexed by Year with monthly and seasonal temperature anomalies (°C)
        relative to the 1951–1980 base period.
        """
        if dataset_key not in GISS_URLS:
            raise ValueError(f"Unknown GISS dataset key: {dataset_key}. Expected one of {list(GISS_URLS.keys())}")

        cache_path = self._get_cache_path(dataset_key)
        csv_text = None

        if not force_refresh and os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    csv_text = f.read()
            except Exception as e:
                logger.warning(f"Error reading GISS cache: {e}")

        if csv_text is None:
            url = GISS_URLS[dataset_key]
            headers = {"User-Agent": "EarthScope-NASA-SpaceApps-2026/1.0 (Team CodeRex)"}
            try:
                resp = requests.get(url, headers=headers, timeout=self.timeout)
                if resp.status_code == 200:
                    csv_text = resp.text
                    if self.cache_enabled:
                        try:
                            with open(cache_path, "w", encoding="utf-8") as f:
                                f.write(csv_text)
                        except Exception as e:
                            logger.warning(f"Failed to cache GISS data: {e}")
                else:
                    raise RuntimeError(f"NASA GISS server returned HTTP {resp.status_code}")
            except Exception as err:
                # If network fails but cache exists, use cache
                if os.path.exists(cache_path):
                    with open(cache_path, "r", encoding="utf-8") as f:
                        csv_text = f.read()
                else:
                    raise RuntimeError(f"Failed to retrieve NASA GISS data: {err}")

        # Parse CSV: Skip the top description title line (e.g. 'Land-Ocean: Global Means')
        lines = csv_text.strip().split("\n")
        header_idx = 0
        for i, line in enumerate(lines[:5]):
            if line.startswith("Year") or "Jan" in line:
                header_idx = i
                break

        clean_csv = "\n".join(lines[header_idx:])
        df = pd.read_csv(io.StringIO(clean_csv))

        # Drop duplicate header lines if repeated in the table
        df = df[df["Year"] != "Year"].copy()

        # Coerce Year and data to numeric
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
        df = df.dropna(subset=["Year"])
        df["Year"] = df["Year"].astype(int)
        df = df.set_index("Year").sort_index()

        # Coerce all columns to numeric, replacing '***' missing flags with NaN
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace("*", "", regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    def get_monthly_anomaly_series(self, dataset_key: str = "global") -> pd.Series:
        """
        Transforms the Year x Month table into a continuous monthly DatetimeIndex Series.
        """
        df = self.fetch_gistemp_data(dataset_key)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        available_months = [m for m in months if m in df.columns]

        records = []
        for year, row in df.iterrows():
            for m_idx, m_name in enumerate(available_months, start=1):
                val = row.get(m_name, np.nan)
                if not np.isnan(val):
                    dt = pd.Timestamp(year=int(year), month=m_idx, day=1)
                    records.append({"date": dt, "anomaly": float(val)})

        res_df = pd.DataFrame(records).set_index("date").sort_index()
        return res_df["anomaly"] if not res_df.empty else pd.Series(dtype=float)
