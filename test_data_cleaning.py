"""
Unit Tests for Data Cleaning and Quality Control
"""

import pytest
import pandas as pd
import numpy as np

from earthscope.data.data_cleaning import parse_and_clean_nasa_data, get_meteorological_season
from earthscope.config import NASA_FILL_VALUE


def test_meteorological_seasons():
    # Northern Hemisphere
    assert get_meteorological_season(1, latitude=20.0) == "Winter"
    assert get_meteorological_season(4, latitude=20.0) == "Spring"
    assert get_meteorological_season(7, latitude=20.0) == "Summer"
    assert get_meteorological_season(10, latitude=20.0) == "Autumn"

    # Southern Hemisphere
    assert get_meteorological_season(1, latitude=-30.0) == "Summer"
    assert get_meteorological_season(4, latitude=-30.0) == "Autumn"
    assert get_meteorological_season(7, latitude=-30.0) == "Winter"
    assert get_meteorological_season(10, latitude=-30.0) == "Spring"


def test_parse_and_clean_nasa_data():
    sample_payload = {
        "_retrieval_metadata": {
            "latitude": 19.9975,
            "longitude": 73.7898
        },
        "properties": {
            "parameter": {
                "T2M": {
                    "20230101": 22.5,
                    "20230102": NASA_FILL_VALUE,  # Should become NaN
                    "20230103": 24.1,
                    "20230104": 150.0  # Physically impossible (>65), should become NaN
                },
                "PRECTOTCORR": {
                    "20230101": 0.0,
                    "20230102": -0.005,  # Tiny negative floating point artifact, should become 0.0
                    "20230103": 12.4,
                    "20230104": -999.0  # Fill value, should become NaN
                }
            }
        }
    }

    df, q_rep = parse_and_clean_nasa_data(sample_payload)

    assert len(df) == 4
    assert isinstance(df.index, pd.DatetimeIndex)

    # Check fill value conversion
    assert np.isnan(df.loc["2023-01-02", "T2M"])
    assert df.loc["2023-01-01", "T2M"] == 22.5
    assert df.loc["2023-01-03", "T2M"] == 24.1

    # Check physical bound mask (>65°C)
    assert np.isnan(df.loc["2023-01-04", "T2M"])

    # Check precipitation artifact zeroing
    assert df.loc["2023-01-02", "PRECTOTCORR"] == 0.0
    assert df.loc["2023-01-03", "PRECTOTCORR"] == 12.4
    assert np.isnan(df.loc["2023-01-04", "PRECTOTCORR"])

    # Check quality report
    assert q_rep["total_days"] == 4
    assert q_rep["variables"]["T2M"]["valid_observations"] == 2
    assert q_rep["variables"]["T2M"]["missing_observations"] == 2
    assert q_rep["variables"]["T2M"]["missing_percentage"] == 50.0
    assert q_rep["variables"]["T2M"]["out_of_bounds_masked"] == 1
