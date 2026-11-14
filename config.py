"""
EarthScope Backend Configuration and Constants
NASA Space Apps Challenge 2026 | Team CodeRex
"""

import os
from typing import Dict, Any, List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "EarthScope API"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "NASA POWER Earth System Trend Explorer Backend"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # NASA POWER API endpoints
    NASA_POWER_MONTHLY_URL: str = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    NASA_POWER_DAILY_URL: str = "https://power.larc.nasa.gov/api/temporal/daily/point"
    NASA_DEFAULT_COMMUNITY: str = "AG"
    NASA_FILL_VALUE: float = -999.0
    
    # Cache settings
    CACHE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "86400"))  # 24 hours default
    CACHE_ENABLED: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Default query settings
    DEFAULT_LOCATION_NAME: str = "Nashik, Maharashtra, India (Featured)"
    DEFAULT_LAT: float = 19.9975
    DEFAULT_LON: float = 73.7898
    DEFAULT_START_YEAR: int = 2015
    DEFAULT_END_YEAR: int = 2025
    MIN_START_YEAR: int = 1981

settings = Settings()

# Supported NASA POWER parameters metadata
PARAMETERS_META: Dict[str, Dict[str, Any]] = {
    "T2M": {
        "name": "Air Temperature at 2m",
        "description": "Monthly or daily average air temperature at 2 meters above surface.",
        "units": "°C",
        "category": "temperature",
        "min_valid": -90.0,
        "max_valid": 65.0,
        "agg_method": "mean"
    },
    "T2M_MAX": {
        "name": "Maximum Air Temperature at 2m",
        "description": "Maximum air temperature at 2 meters above surface.",
        "units": "°C",
        "category": "temperature",
        "min_valid": -80.0,
        "max_valid": 70.0,
        "agg_method": "mean"
    },
    "T2M_MIN": {
        "name": "Minimum Air Temperature at 2m",
        "description": "Minimum air temperature at 2 meters above surface.",
        "units": "°C",
        "category": "temperature",
        "min_valid": -95.0,
        "max_valid": 60.0,
        "agg_method": "mean"
    },
    "PRECTOTCORR": {
        "name": "Corrected Precipitation",
        "description": "Precipitation amount (accumulated mm/month or mm/day rate).",
        "units": "mm",
        "category": "precipitation",
        "min_valid": 0.0,
        "max_valid": 2500.0,
        "agg_method": "sum"
    },
    "RH2M": {
        "name": "Relative Humidity at 2m",
        "description": "Relative humidity percentage at 2 meters.",
        "units": "%",
        "category": "atmosphere",
        "min_valid": 0.0,
        "max_valid": 100.0,
        "agg_method": "mean"
    },
    "TS": {
        "name": "Earth Skin Temperature",
        "description": "Radiative surface skin temperature of the land/water surface.",
        "units": "°C",
        "category": "land",
        "min_valid": -90.0,
        "max_valid": 75.0,
        "agg_method": "mean"
    },
    "WS2M": {
        "name": "Wind Speed at 2m",
        "description": "Average horizontal wind speed at 2 meters above ground level.",
        "units": "m/s",
        "category": "atmosphere",
        "min_valid": 0.0,
        "max_valid": 75.0,
        "agg_method": "mean"
    },
    "ALLSKY_SFC_SW_DWN": {
        "name": "All Sky Surface Downward Solar Irradiance",
        "description": "Total downward solar irradiance incident on horizontal surface.",
        "units": "MJ/m²/day",
        "category": "radiation",
        "min_valid": 0.0,
        "max_valid": 45.0,
        "agg_method": "mean"
    }
}

# Catalog of global benchmark locations
LOCATION_PRESETS: List[Dict[str, Any]] = [
    {
        "id": "nashik",
        "name": "Nashik, Maharashtra, India (Featured)",
        "short_name": "Nashik, India",
        "lat": 19.9975,
        "lon": 73.7898,
        "region": "South Asia",
        "biome": "Tropical Wet-and-Dry / Viticulture Hub",
        "significance": "Crucial viticultural and agricultural basin with seasonal South Asian monsoon shifts.",
        "featured": True
    },
    {
        "id": "mumbai",
        "name": "Mumbai, India",
        "short_name": "Mumbai",
        "lat": 19.0760,
        "lon": 72.8777,
        "region": "South Asia",
        "biome": "Tropical Coastal Monsoon",
        "significance": "Dense coastal megacity sensitive to sea surface temperatures and monsoon cloud bursts.",
        "featured": False
    },
    {
        "id": "delhi",
        "name": "Delhi, India",
        "short_name": "Delhi",
        "lat": 28.6139,
        "lon": 77.2090,
        "region": "South Asia",
        "biome": "Semi-Arid Continental",
        "significance": "Northern Indian plains with extreme winter fog inversions and searing summer heatwaves.",
        "featured": False
    },
    {
        "id": "london",
        "name": "London, United Kingdom",
        "short_name": "London",
        "lat": 51.5074,
        "lon": -0.1278,
        "region": "Western Europe",
        "biome": "Temperate Oceanic",
        "significance": "Centuries-long Atlantic maritime climate record witnessing unprecedented heat extremes.",
        "featured": False
    },
    {
        "id": "cairo",
        "name": "Cairo, Egypt",
        "short_name": "Cairo",
        "lat": 30.0444,
        "lon": 31.2357,
        "region": "North Africa",
        "biome": "Hyper-Arid Subtropical",
        "significance": "Nile delta civilization observing expanding desertification and extreme water stress.",
        "featured": False
    },
    {
        "id": "nairobi",
        "name": "Nairobi, Kenya",
        "short_name": "Nairobi",
        "lat": -1.2921,
        "lon": 36.8219,
        "region": "East Africa",
        "biome": "Subtropical Highland",
        "significance": "Equatorial highland experiencing bimodal rainfall patterns and East African drought cycles.",
        "featured": False
    },
    {
        "id": "capetown",
        "name": "Cape Town, South Africa",
        "short_name": "Cape Town",
        "lat": -33.9249,
        "lon": 18.4241,
        "region": "Southern Africa",
        "biome": "Mediterranean Coastal",
        "significance": "Vulnerable coastal watershed famously impacted by the multi-year 'Day Zero' drought cycle.",
        "featured": False
    },
    {
        "id": "newyork",
        "name": "New York, USA",
        "short_name": "New York",
        "lat": 40.7128,
        "lon": -74.0060,
        "region": "North America",
        "biome": "Humid Subtropical / Megacity",
        "significance": "Atlantic coastal megalopolis observing increasing high-intensity precipitation events.",
        "featured": False
    },
    {
        "id": "mexicocity",
        "name": "Mexico City, Mexico",
        "short_name": "Mexico City",
        "lat": 19.4326,
        "lon": -99.1332,
        "region": "Central America",
        "biome": "Highland Subtropical",
        "significance": "High-altitude basin metropolis facing acute groundwater depletion and urban thermal trapping.",
        "featured": False
    },
    {
        "id": "saopaulo",
        "name": "São Paulo, Brazil",
        "short_name": "São Paulo",
        "lat": -23.5505,
        "lon": -46.6333,
        "region": "South America",
        "biome": "Humid Subtropical Highland",
        "significance": "Major economic engine prone to Atlantic rainforest deforestation microclimate feedback.",
        "featured": False
    },
    {
        "id": "tokyo",
        "name": "Tokyo, Japan",
        "short_name": "Tokyo",
        "lat": 35.6762,
        "lon": 139.6503,
        "region": "East Asia",
        "biome": "Urban Temperate Maritime",
        "significance": "Dense megalopolis showcasing urban heat island interactions with Pacific typhoon rainfall.",
        "featured": False
    },
    {
        "id": "beijing",
        "name": "Beijing, China",
        "short_name": "Beijing",
        "lat": 39.9042,
        "lon": 116.4074,
        "region": "East Asia",
        "biome": "Monsoon-Influenced Continental",
        "significance": "Continental Asian climate marked by hot humid summers and cold dry Siberian anticyclone winters.",
        "featured": False
    },
    {
        "id": "sydney",
        "name": "Sydney, Australia",
        "short_name": "Sydney",
        "lat": -33.8688,
        "lon": 151.2093,
        "region": "Oceania",
        "biome": "Subtropical Coastal",
        "significance": "Subject to intense El Niño–Southern Oscillation (ENSO) rainfall swings and bushfire seasons.",
        "featured": False
    },
    {
        "id": "reykjavik",
        "name": "Reykjavik, Iceland",
        "short_name": "Reykjavik",
        "lat": 64.1466,
        "lon": -21.9426,
        "region": "Subpolar North Atlantic",
        "biome": "Subpolar Oceanic",
        "significance": "Near-Arctic volcanic island directly impacted by North Atlantic subpolar gyre variability.",
        "featured": False
    },
    {
        "id": "singapore",
        "name": "Singapore",
        "short_name": "Singapore",
        "lat": 1.3521,
        "lon": 103.8198,
        "region": "Southeast Asia",
        "biome": "Equatorial Rainforest",
        "significance": "Hyper-dense equatorial island with year-round tropical convective rainfall and minimal seasonality.",
        "featured": False
    },
    {
        "id": "manaus",
        "name": "Manaus, Amazon Basin, Brazil",
        "short_name": "Amazon Basin",
        "lat": -3.1190,
        "lon": -60.0210,
        "region": "South America",
        "biome": "Equatorial Rainforest",
        "significance": "Heart of the Amazon rainforest observing extreme hydrological cycles and heat stress.",
        "featured": False
    },
    {
        "id": "longyearbyen",
        "name": "Longyearbyen, Svalbard (Arctic)",
        "short_name": "Svalbard Arctic",
        "lat": 78.2232,
        "lon": 15.6469,
        "region": "Arctic High North",
        "biome": "Arctic Tundra / Permafrost",
        "significance": "One of the fastest-warming settlements on Earth experiencing rapid polar amplification.",
        "featured": False
    },
    {
        "id": "deathvalley",
        "name": "Furnace Creek, Death Valley, USA",
        "short_name": "Death Valley",
        "lat": 36.4631,
        "lon": -116.8672,
        "region": "North America",
        "biome": "Hyper-Arid Terrestrial Extreme",
        "significance": "Global benchmark for extreme terrestrial heat and hyper-arid evaporative limits.",
        "featured": False
    }
]
