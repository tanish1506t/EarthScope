"""
Tests for Report Generation (CSV and PDF)
"""

import pytest
from backend.app.schemas import ClimateRecord, ClimateSummary, TrendResult, AnomaliesResponse
from backend.app.services.report_service import ReportService

def test_generate_csv():
    records = [
        ClimateRecord(date="2024-01", year=2024, month=1, t2m=22.5, prectotcorr=12.0),
        ClimateRecord(date="2024-02", year=2024, month=2, t2m=24.1, prectotcorr=5.5)
    ]
    csv_str = ReportService.generate_csv(records, "Nashik, India", 19.9975, 73.7898, "2024-01-01T00:00:00Z")
    
    assert "EARTHSCOPE CLIMATE DATA DOSSIER" in csv_str
    assert "Nashik, India" in csv_str
    assert "2024-01" in csv_str
    assert "22.5" in csv_str

def test_generate_pdf():
    records = [ClimateRecord(date="2024-01", year=2024, month=1, t2m=22.5, prectotcorr=12.0)]
    summary = ClimateSummary(mean_temperature=22.5, total_records=1, valid_records=1)
    trend = TrendResult(
        parameter="T2M",
        parameter_name="Air Temperature",
        units="°C",
        n_observations=1,
        slope_per_year=0.05,
        slope_per_decade=0.5,
        direction="warming",
        is_significant=False,
        verdict="Testing trend verdict"
    )
    anomalies = AnomaliesResponse(
        variable="T2M",
        units="°C",
        baseline_period="2024",
        total_months=1,
        extreme_count=0,
        all_anomalies=[],
        flagged_anomalies=[],
        monthly_climatology={}
    )

    pdf_bytes = ReportService.generate_pdf(
        location_name="Nashik, India",
        lat=19.9975,
        lon=73.7898,
        summary=summary,
        trend=trend,
        anomalies=anomalies,
        records=records
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")
