"""
Tests for NASA POWER Service (Caching, Keys, Validation)
"""

import os
import pytest
from backend.app.services.nasa_power import NASAPowerService

def test_cache_key_generation(tmp_path):
    service = NASAPowerService()
    key1 = service._generate_cache_key(19.9975, 73.7898, 2015, 2024, ["T2M", "PRECTOTCORR"], "monthly")
    # Order of parameters should not change key
    key2 = service._generate_cache_key(19.9975, 73.7898, 2015, 2024, ["PRECTOTCORR", "T2M"], "monthly")
    assert key1 == key2
    assert len(key1) == 64

def test_cache_read_write(tmp_path):
    service = NASAPowerService()
    service.cache_dir = str(tmp_path)
    test_key = "test_cache_key_abc123"
    dummy_payload = {
        "properties": {"parameter": {"T2M": {"202401": 21.5}}},
        "_retrieval_metadata": {"source": "NASA POWER Test"}
    }
    
    # Write
    service._write_cache(test_key, dummy_payload)
    
    # Read
    cached = service._read_cache(test_key)
    assert cached is not None
    assert cached["_from_cache"] is True
    assert cached["properties"]["parameter"]["T2M"]["202401"] == 21.5
