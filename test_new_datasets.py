"""
Unit Tests for Additional NASA Datasets (NASA GISTEMP v4 & MODIS NDVI)
"""

import pytest
import pandas as pd
import numpy as np

from earthscope.data.nasa_giss_client import NASAGissClient
from earthscope.data.modis_ndvi_client import generate_calibrated_modis_ndvi


def test_modis_ndvi_generation():
    df = generate_calibrated_modis_ndvi(lat=19.9975, lon=73.7898, start_year=2020, end_year=2023)

    assert not df.empty
    assert isinstance(df.index, pd.DatetimeIndex)
    assert "NDVI" in df.columns
    assert "EVI" in df.columns
    assert "VCI" in df.columns
    assert "NDVI_NORMAL" in df.columns
    assert "NDVI_ANOMALY" in df.columns

    # Valid physical ranges
    assert df["NDVI"].min() >= 0.0
    assert df["NDVI"].max() <= 1.0
    assert df["VCI"].min() >= 0.0
    assert df["VCI"].max() <= 100.0

    # Composite step is 16 days
    diff_days = (df.index[1] - df.index[0]).days
    assert diff_days == 16


def test_nasa_giss_parser(tmp_path):
    # Test GISS parser with sample CSV structure matching official NASA GISS table
    sample_csv = """Land-Ocean: Global Means
Year,Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec,J-D,D-N,DJF,MAM,JJA,SON
2020,.76,1.01,.98,.89,.92,.85,.86,.84,.89,.82,.91,.78,.88,.88,.85,.93,.85,.87
2021,.75,.64,.73,.76,.68,.71,.71,.72,.70,.84,.84,.75,.74,.74,.72,.72,.71,.79
2022,.79,.78,.87,.73,.67,.76,.77,.81,.78,.81,.67,.67,.76,.77,.77,.76,.78,.75
2023,.77,.86,.80,.76,.82,.94,1.08,1.09,1.37,1.25,1.33,1.25,1.08,1.04,.77,.79,1.04,1.32
"""
    cache_dir = str(tmp_path / "giss_test")
    client = NASAGissClient(cache_enabled=True, cache_dir=cache_dir)
    cache_file = client._get_cache_path("global")
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(sample_csv)

    df = client.fetch_gistemp_data("global", force_refresh=False)
    assert len(df) == 4
    assert df.index.min() == 2020
    assert df.index.max() == 2023
    assert df.loc[2023, "J-D"] == 1.08

    s = client.get_monthly_anomaly_series("global")
    assert len(s) == 48  # 4 years * 12 months
    assert s.loc["2023-07-01"] == 1.08
