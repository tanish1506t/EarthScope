"""
Reports API Router
Generates downloadable CSV data dossiers and publication-quality PDF investigation reports.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Response

from backend.app.config import settings, LOCATION_PRESETS
from backend.app.services.nasa_power import nasa_service
from backend.app.services.climate_processing import climate_service
from backend.app.services.statistics import statistics_service
from backend.app.services.anomaly_detection import anomaly_service
from backend.app.services.report_service import report_service
from backend.app.api.routes_climate import resolve_location_name

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/csv")
async def download_csv_report(
    lat: float = Query(settings.DEFAULT_LAT, ge=-90.0, le=90.0),
    lon: float = Query(settings.DEFAULT_LON, ge=-180.0, le=180.0),
    start_year: int = Query(settings.DEFAULT_START_YEAR, ge=1981, le=2026),
    end_year: int = Query(settings.DEFAULT_END_YEAR, ge=1981, le=2026),
    location_name: Optional[str] = Query(None)
):
    """
    Exports processed and quality-controlled monthly climate observations as a formatted CSV dossier.
    """
    loc_name = resolve_location_name(lat, lon, location_name)
    try:
        raw_payload = await nasa_service.fetch_monthly_data(
            lat=lat,
            lon=lon,
            start_year=start_year,
            end_year=end_year
        )
        records, summary, df = climate_service.process_monthly_payload(raw_payload, loc_name)
        retrieval_time = raw_payload.get("_retrieval_metadata", {}).get("retrieved_at", datetime.utcnow().isoformat())

        csv_content = report_service.generate_csv(
            records=records,
            location_name=loc_name,
            lat=lat,
            lon=lon,
            retrieval_time=retrieval_time
        )

        clean_slug = loc_name.split(",")[0].lower().replace(" ", "_")
        filename = f"earthscope_{clean_slug}_{start_year}_{end_year}.csv"

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV dossier: {str(e)}")

@router.get("/pdf")
async def download_pdf_report(
    lat: float = Query(settings.DEFAULT_LAT, ge=-90.0, le=90.0),
    lon: float = Query(settings.DEFAULT_LON, ge=-180.0, le=180.0),
    start_year: int = Query(settings.DEFAULT_START_YEAR, ge=1981, le=2026),
    end_year: int = Query(settings.DEFAULT_END_YEAR, ge=1981, le=2026),
    location_name: Optional[str] = Query(None)
):
    """
    Generates a publication-grade scientific PDF investigation dossier.
    """
    loc_name = resolve_location_name(lat, lon, location_name)
    try:
        raw_payload = await nasa_service.fetch_monthly_data(
            lat=lat,
            lon=lon,
            start_year=start_year,
            end_year=end_year
        )
        records, summary, df = climate_service.process_monthly_payload(raw_payload, loc_name)
        trend = statistics_service.calculate_trend(df, "t2m", "yearly")
        anomalies = anomaly_service.detect_anomalies(df, "t2m")

        pdf_bytes = report_service.generate_pdf(
            location_name=loc_name,
            lat=lat,
            lon=lon,
            summary=summary,
            trend=trend,
            anomalies=anomalies,
            records=records
        )

        clean_slug = loc_name.split(",")[0].lower().replace(" ", "_")
        filename = f"earthscope_investigation_{clean_slug}_{start_year}_{end_year}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compile PDF report: {str(e)}")
