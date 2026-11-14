"""
Climate Data API Router
Endpoints for fetching validated NASA POWER monthly time-series and multi-location comparisons.
"""

from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException

from backend.app.config import settings, LOCATION_PRESETS, PARAMETERS_META
from backend.app.schemas import ClimateResponse, ClimateCompareResponse, ClimateCompareItem
from backend.app.services.nasa_power import nasa_service
from backend.app.services.climate_processing import climate_service

router = APIRouter(prefix="/api/climate", tags=["Climate"])

def resolve_location_name(lat: float, lon: float, provided_name: Optional[str]) -> str:
    if provided_name and provided_name.strip():
        return provided_name.strip()
    # Check closest preset
    for loc in LOCATION_PRESETS:
        if abs(loc["lat"] - lat) < 0.2 and abs(loc["lon"] - lon) < 0.2:
            return loc["name"]
    return f"Coord ({lat:.2f}°, {lon:.2f}°)"

@router.get("", response_model=ClimateResponse)
async def get_climate_data(
    lat: float = Query(settings.DEFAULT_LAT, ge=-90.0, le=90.0, description="Latitude in decimal degrees"),
    lon: float = Query(settings.DEFAULT_LON, ge=-180.0, le=180.0, description="Longitude in decimal degrees"),
    start_year: int = Query(settings.DEFAULT_START_YEAR, ge=1981, le=2026, description="Start year"),
    end_year: int = Query(settings.DEFAULT_END_YEAR, ge=1981, le=2026, description="End year"),
    parameters: Optional[str] = Query(None, description="Comma-separated parameters e.g. T2M,PRECTOTCORR"),
    location_name: Optional[str] = Query(None, description="Human readable location name"),
    force_refresh: bool = Query(False, description="Bypass cache")
):
    """
    Retrieves validated monthly climate records directly from NASA POWER API.
    """
    if start_year > end_year:
        raise HTTPException(status_code=400, detail="start_year cannot be greater than end_year.")

    param_list = [p.strip().upper() for p in parameters.split(",")] if parameters else None
    loc_name = resolve_location_name(lat, lon, location_name)

    try:
        raw_payload = await nasa_service.fetch_monthly_data(
            lat=lat,
            lon=lon,
            start_year=start_year,
            end_year=end_year,
            parameters=param_list,
            force_refresh=force_refresh
        )

        records, summary, df = climate_service.process_monthly_payload(raw_payload, loc_name)

        return ClimateResponse(
            status="success",
            location_name=loc_name,
            latitude=lat,
            longitude=lon,
            temporal_resolution="monthly",
            start_year=start_year,
            end_year=end_year,
            summary=summary,
            records=records,
            retrieval_metadata=raw_payload.get("_retrieval_metadata", {})
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to retrieve or process NASA POWER data: {str(e)}")

@router.get("/compare", response_model=ClimateCompareResponse)
async def compare_locations(
    parameter: str = Query("t2m", description="Parameter to compare (t2m or prectotcorr)"),
    location_ids: Optional[str] = Query(None, description="Comma-separated location IDs to compare"),
    start_year: int = Query(settings.DEFAULT_START_YEAR, ge=1981, le=2026),
    end_year: int = Query(settings.DEFAULT_END_YEAR, ge=1981, le=2026)
):
    """
    Compares climatological indicators across multiple benchmark locations.
    """
    param_col = parameter.lower()
    meta = PARAMETERS_META.get(parameter.upper(), {})
    units = meta.get("units", "°C")
    param_name = meta.get("name", parameter)

    target_locations = []
    if location_ids:
        req_ids = [lid.strip().lower() for lid in location_ids.split(",")]
        for loc in LOCATION_PRESETS:
            if loc["id"].lower() in req_ids or loc["short_name"].lower() in req_ids:
                target_locations.append(loc)
    
    if not target_locations:
        # Default to first 5 presets
        target_locations = LOCATION_PRESETS[:5]

    compare_items: List[ClimateCompareItem] = []

    for loc in target_locations:
        try:
            raw_payload = await nasa_service.fetch_monthly_data(
                lat=loc["lat"],
                lon=loc["lon"],
                start_year=start_year,
                end_year=end_year
            )
            records, summary, df = climate_service.process_monthly_payload(raw_payload, loc["name"])

            if not df.empty and param_col in df.columns:
                series = df[param_col].dropna()
                mean_v = round(float(series.mean()), 2) if not series.empty else None
                min_v = round(float(series.min()), 2) if not series.empty else None
                max_v = round(float(series.max()), 2) if not series.empty else None
                
                # Annual breakdown
                if param_col == "prectotcorr":
                    annual_s = df.groupby("year")[param_col].sum()
                else:
                    annual_s = df.groupby("year")[param_col].mean()

                ann_list = [{"year": int(y), "value": round(float(v), 2)} for y, v in annual_s.items()]
            else:
                mean_v, min_v, max_v = None, None, None
                ann_list = []

            compare_items.append(ClimateCompareItem(
                location_name=loc["short_name"],
                latitude=loc["lat"],
                longitude=loc["lon"],
                mean_value=mean_v,
                min_value=min_v,
                max_value=max_v,
                total_records=len(records),
                annual_series=ann_list
            ))
        except Exception:
            # Add entry with nulls if a location fails
            compare_items.append(ClimateCompareItem(
                location_name=loc["short_name"],
                latitude=loc["lat"],
                longitude=loc["lon"],
                total_records=0,
                annual_series=[]
            ))

    return ClimateCompareResponse(
        parameter=parameter,
        parameter_name=param_name,
        units=units,
        period=f"{start_year}–{end_year}",
        locations=compare_items
    )
