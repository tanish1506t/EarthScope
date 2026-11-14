"""
Scientific Analysis API Router
Provides trend analysis, descriptive statistics, anomaly detection, and empirical projections.
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from backend.app.config import settings, LOCATION_PRESETS
from backend.app.schemas import (
    TrendResult, DescriptiveStatistics,
    AnomaliesResponse, ProjectionsResponse
)
from backend.app.services.nasa_power import nasa_service
from backend.app.services.climate_processing import climate_service
from backend.app.services.statistics import statistics_service
from backend.app.services.anomaly_detection import anomaly_service

router = APIRouter(prefix="/api/analysis", tags=["Scientific Analysis"])

async def get_dataframe_for_query(lat: float, lon: float, start_year: int, end_year: int):
    payload = await nasa_service.fetch_monthly_data(
        lat=lat,
        lon=lon,
        start_year=start_year,
        end_year=end_year
    )
    records, summary, df = climate_service.process_monthly_payload(payload, f"Coord ({lat},{lon})")
    return df

@router.get("/trends", response_model=TrendResult)
async def get_trends(
    lat: float = Query(settings.DEFAULT_LAT, ge=-90.0, le=90.0),
    lon: float = Query(settings.DEFAULT_LON, ge=-180.0, le=180.0),
    start_year: int = Query(settings.DEFAULT_START_YEAR, ge=1981, le=2026),
    end_year: int = Query(settings.DEFAULT_END_YEAR, ge=1981, le=2026),
    parameter: str = Query("t2m", description="Parameter to evaluate: t2m, prectotcorr, etc."),
    temporal_group: str = Query("yearly", description="Aggregation: 'yearly' or 'monthly'")
):
    """
    Computes OLS linear regression, Sen's slope estimator, and Mann-Kendall monotonic trend test.
    """
    try:
        df = await get_dataframe_for_query(lat, lon, start_year, end_year)
        result = statistics_service.calculate_trend(df, parameter, temporal_group)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate trend analysis: {str(e)}")

@router.get("/statistics", response_model=DescriptiveStatistics)
async def get_statistics(
    lat: float = Query(settings.DEFAULT_LAT, ge=-90.0, le=90.0),
    lon: float = Query(settings.DEFAULT_LON, ge=-180.0, le=180.0),
    start_year: int = Query(settings.DEFAULT_START_YEAR, ge=1981, le=2026),
    end_year: int = Query(settings.DEFAULT_END_YEAR, ge=1981, le=2026),
    parameter: str = Query("t2m")
):
    """
    Computes rigorous descriptive metrics: mean, median, std dev, IQR, skewness, kurtosis, and distribution histogram.
    """
    try:
        df = await get_dataframe_for_query(lat, lon, start_year, end_year)
        col = parameter.lower()
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Parameter '{parameter}' not found in dataset.")
        stats_result = statistics_service.calculate_descriptive_stats(df[col], parameter)
        return stats_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute statistics: {str(e)}")

@router.get("/anomalies", response_model=AnomaliesResponse)
async def get_anomalies(
    lat: float = Query(settings.DEFAULT_LAT, ge=-90.0, le=90.0),
    lon: float = Query(settings.DEFAULT_LON, ge=-180.0, le=180.0),
    start_year: int = Query(settings.DEFAULT_START_YEAR, ge=1981, le=2026),
    end_year: int = Query(settings.DEFAULT_END_YEAR, ge=1981, le=2026),
    parameter: str = Query("t2m")
):
    """
    Calculates calendar-month climatological baseline departures and flags extreme events (|z| > 2.0).
    """
    try:
        df = await get_dataframe_for_query(lat, lon, start_year, end_year)
        anomalies_result = anomaly_service.detect_anomalies(df, parameter)
        return anomalies_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute anomalies: {str(e)}")

@router.get("/projections", response_model=ProjectionsResponse)
async def get_projections(
    lat: float = Query(settings.DEFAULT_LAT, ge=-90.0, le=90.0),
    lon: float = Query(settings.DEFAULT_LON, ge=-180.0, le=180.0),
    start_year: int = Query(settings.DEFAULT_START_YEAR, ge=1981, le=2026),
    end_year: int = Query(settings.DEFAULT_END_YEAR, ge=1981, le=2026),
    parameter: str = Query("t2m"),
    horizon_years: int = Query(5, ge=1, le=10, description="Projection horizon in years (1 to 10)")
):
    """
    Produces empirical straight-line trend projections with prediction intervals and explicit scientific caveats.
    """
    try:
        df = await get_dataframe_for_query(lat, lon, start_year, end_year)
        projections_result = anomaly_service.project_trends(df, parameter, horizon_years)
        return projections_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate projections: {str(e)}")
