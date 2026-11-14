"""
Tests for Anomaly Detection and Projections
"""

import pytest
import numpy as np
import pandas as pd
from backend.app.services.anomaly_detection import AnomalyDetectionService

def test_anomaly_detection_with_extreme_flag():
    rows = []
    # 5 years of baseline data
    for y in range(2018, 2023):
        for m in range(1, 13):
            val = 25.0 + (5.0 if m in (5, 6) else 0.0)
            rows.append({"year": y, "month": m, "t2m": val})

    # Add an extreme heat spike in May 2023 (+10 degrees above typical May)
    rows.append({"year": 2023, "month": 5, "t2m": 40.0})

    df = pd.DataFrame(rows)
    anom_res = AnomalyDetectionService.detect_anomalies(df, "t2m")

    assert anom_res.total_months == len(rows)
    # The May 2023 spike should be flagged
    assert anom_res.extreme_count >= 1
    top_flag = anom_res.flagged_anomalies[0]
    assert top_flag.year == 2023 and top_flag.month == 5
    assert top_flag.is_extreme is True
    assert top_flag.z_score > 2.0
    assert "warmer" in top_flag.insight

def test_trend_projections():
    rows = []
    for y in range(2015, 2025):
        for m in range(1, 13):
            rows.append({"year": y, "month": m, "t2m": 20.0 + 0.2 * (y - 2015)})
    df = pd.DataFrame(rows)

    proj = AnomalyDetectionService.project_trends(df, "t2m", horizon_years=5)
    assert proj.projected_horizon_years == 5
    assert proj.historical_start_year == 2015
    assert proj.historical_end_year == 2024
    
    # 10 historical + 5 projected = 15 records
    assert len(proj.records) == 15
    assert proj.records[-1].type == "projected"
    assert proj.records[-1].year == 2029
    assert proj.records[-1].ci_lower is not None
    assert proj.records[-1].ci_upper is not None
    assert "SCIENTIFIC NOTICE" in proj.methodology_disclaimer
