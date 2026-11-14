"""
Tests for Climate Processing Service (Payload Parsing, Units, Precipitation Aggregation)
"""

import pytest
import pandas as pd
from backend.app.services.climate_processing import ClimateProcessingService

def test_process_monthly_payload_and_units():
    # Synthetic NASA POWER monthly mock payload with month 13 (annual) and -999 fill values
    payload = {
        "properties": {
            "parameter": {
                "T2M": {
                    "202301": 20.0,
                    "202302": 22.0,
                    "202303": -999.0,  # Missing
                    "202313": 21.0     # Annual summary from NASA, should be ignored for monthly series
                },
                "PRECTOTCORR": {
                    "202301": 2.0,     # 2 mm/day in Jan (31 days) -> 62.0 mm
                    "202302": 1.5,     # 1.5 mm/day in Feb 2023 (28 days) -> 42.0 mm
                    "202303": 0.0,     # 0 mm/day in Mar (31 days) -> 0.0 mm
                    "202313": 1.2
                }
            }
        },
        "_retrieval_metadata": {"latitude": 19.9975, "longitude": 73.7898}
    }

    records, summary, df = ClimateProcessingService.process_monthly_payload(payload, "Test City")
    
    # Check that '13' is filtered out
    assert len(records) == 3
    assert records[0].date == "2023-01"
    assert records[1].date == "2023-02"
    assert records[2].date == "2023-03"

    # Check missing value quarantined as None (never 0.0)
    assert records[2].t2m is None

    # Check precipitation calculation: mm/day * days_in_month
    assert records[0].prectotcorr == 62.0  # 2.0 * 31
    assert records[1].prectotcorr == 42.0  # 1.5 * 28
    assert records[2].prectotcorr == 0.0   # 0.0 * 31

    # Check summary
    assert summary.total_records == 3
    assert summary.valid_records == 2  # 20.0 and 22.0
    assert summary.mean_temperature == 21.0
    assert summary.max_temperature == 22.0
    assert summary.min_temperature == 20.0
