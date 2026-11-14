"""
Locations API Router
Provides location benchmarks, presets, and geographic coordinate lookup.
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from backend.app.config import LOCATION_PRESETS, settings
from backend.app.schemas import LocationListResponse, LocationItem

router = APIRouter(prefix="/api/locations", tags=["Locations"])

@router.get("", response_model=LocationListResponse)
async def get_locations(featured_only: bool = False):
    """
    Returns available location presets including coordinates, biome types, and climatological significance.
    """
    items = LOCATION_PRESETS
    if featured_only:
        items = [loc for loc in items if loc.get("featured", False)]
    
    locations = [LocationItem(**loc) for loc in items]
    return LocationListResponse(
        total=len(locations),
        default_location_id="nashik",
        locations=locations
    )

@router.get("/{location_id}", response_model=LocationItem)
async def get_location_by_id(location_id: str):
    """
    Returns specific location preset by its unique ID.
    """
    for loc in LOCATION_PRESETS:
        if loc["id"].lower() == location_id.lower():
            return LocationItem(**loc)
    raise HTTPException(status_code=404, detail=f"Location '{location_id}' not found.")
