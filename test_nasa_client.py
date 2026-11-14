"""
Unit Tests for NASA POWER API Client Validation and Caching
"""

import os
import pytest
from earthscope.data.nasa_power_client import NASAPowerClient, NASADataRetrievalError


def test_client_input_validation():
    client = NASAPowerClient(cache_enabled=False)

    # Valid inputs
    s_str, e_str = client.validate_inputs(lat=19.9975, lon=73.7898, start="2020-01-01", end="2023-12-31")
    assert s_str == "20200101"
    assert e_str == "20231231"

    # Out of bound latitude
    with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
        client.validate_inputs(lat=95.0, lon=0.0, start="20200101", end="20200102")

    # Out of bound longitude
    with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
        client.validate_inputs(lat=0.0, lon=190.0, start="20200101", end="20200102")

    # Chronologically reversed dates
    with pytest.raises(ValueError, match="cannot be chronologically after end date"):
        client.validate_inputs(lat=0.0, lon=0.0, start="20230101", end="20200101")

    # Start date before modern record (1981)
    with pytest.raises(ValueError, match="modern meteorological records start at 1981"):
        client.validate_inputs(lat=0.0, lon=0.0, start="19700101", end="19750101")


def test_client_caching(tmp_path):
    cache_dir = str(tmp_path / "test_cache")
    client = NASAPowerClient(cache_enabled=True, cache_dir=cache_dir)

    key = client._generate_cache_key(19.9975, 73.7898, "20230101", "20230105", ["T2M"])
    assert isinstance(key, str) and len(key) == 64

    # Write dummy to cache
    dummy_payload = {"properties": {"parameter": {"T2M": {"20230101": 22.0}}}}
    client._write_to_cache(key, dummy_payload)

    # Read back from cache
    read_data = client._read_from_cache(key)
    assert read_data is not None
    assert read_data["_from_cache"] is True
    assert read_data["properties"]["parameter"]["T2M"]["20230101"] == 22.0

    # Clear cache
    cleared_count = client.clear_cache()
    assert cleared_count == 1
    assert client._read_from_cache(key) is None
