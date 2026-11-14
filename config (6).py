"""
Configuration and constants for EarthScope - Earth Trend Explorer.
NASA Space Apps Challenge 2026 | Team CodeRex
"""

from typing import Dict, Any

APP_NAME = "EarthScope"
APP_SUBTITLE = "Earth System Trend Detective"
APP_TAGLINE = "Investigate planetary environmental shifts with authentic NASA Earth observations & rigorous statistical analytics."
TEAM_NAME = "CodeRex"
CHALLENGE_TITLE = "NASA Space Apps Challenge 2026: Be An Earth System Trend Detective!"

# NASA POWER API configuration
NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
DEFAULT_COMMUNITY = "AG"  # Agroclimatology / environmental
NASA_FILL_VALUE = -999.0

# Supported NASA POWER parameters with metadata
PARAMETERS_META: Dict[str, Dict[str, Any]] = {
    "T2M": {
        "name": "Mean Temperature at 2m",
        "description": "Daily average air temperature at 2 meters above Earth's surface.",
        "units": "°C",
        "category": "temperature",
        "min_valid": -90.0,
        "max_valid": 65.0,
        "color": "#00f0ff",
        "agg_method": "mean"
    },
    "T2M_MAX": {
        "name": "Maximum Temperature at 2m",
        "description": "Daily maximum air temperature at 2 meters above Earth's surface.",
        "units": "°C",
        "category": "temperature",
        "min_valid": -80.0,
        "max_valid": 70.0,
        "color": "#f43f5e",
        "agg_method": "mean"
    },
    "T2M_MIN": {
        "name": "Minimum Temperature at 2m",
        "description": "Daily minimum air temperature at 2 meters above Earth's surface.",
        "units": "°C",
        "category": "temperature",
        "min_valid": -95.0,
        "max_valid": 60.0,
        "color": "#38bdf8",
        "agg_method": "mean"
    },
    "PRECTOTCORR": {
        "name": "Corrected Precipitation",
        "description": "Daily bias-corrected total precipitation amount.",
        "units": "mm/day",
        "category": "precipitation",
        "min_valid": 0.0,
        "max_valid": 800.0,
        "color": "#10b981",
        "agg_method": "sum"
    },
    "ALLSKY_SFC_SW_DWN": {
        "name": "All Sky Surface Downward Solar Irradiance",
        "description": "Total solar irradiance incident on a horizontal surface under all sky conditions.",
        "units": "MJ/m²/day",
        "category": "radiation",
        "min_valid": 0.0,
        "max_valid": 45.0,
        "color": "#f59e0b",
        "agg_method": "mean"
    },
    "TS": {
        "name": "Earth Skin Temperature",
        "description": "Radiative surface skin temperature of the land/water surface.",
        "units": "°C",
        "category": "land",
        "min_valid": -90.0,
        "max_valid": 75.0,
        "color": "#a855f7",
        "agg_method": "mean"
    },
    "GWETROOT": {
        "name": "Root Zone Soil Wetness",
        "description": "Relative soil moisture in the root zone (0 = dry, 1 = saturated).",
        "units": "fraction (0-1)",
        "category": "land",
        "min_valid": 0.0,
        "max_valid": 1.0,
        "color": "#06b6d4",
        "agg_method": "mean"
    },
    "RH2M": {
        "name": "Relative Humidity at 2m",
        "description": "Ratio of actual water vapor pressure to saturation vapor pressure at 2 meters.",
        "units": "%",
        "category": "atmosphere",
        "min_valid": 0.0,
        "max_valid": 100.0,
        "color": "#38bdf8",
        "agg_method": "mean"
    },
    "WS2M": {
        "name": "Wind Speed at 2m",
        "description": "Average horizontal wind speed at 2 meters above ground level.",
        "units": "m/s",
        "category": "atmosphere",
        "min_valid": 0.0,
        "max_valid": 75.0,
        "color": "#f59e0b",
        "agg_method": "mean"
    }
}

# Pre-configured global benchmark locations
LOCATION_PRESETS: Dict[str, Dict[str, Any]] = {
    "Nashik, Maharashtra, India (Featured)": {
        "lat": 19.9975,
        "lon": 73.7898,
        "region": "South Asia",
        "biome": "Tropical Wet-and-Dry / Agricultural Agro-zone",
        "significance": "Crucial viticultural and agricultural hub experiencing rapid seasonal monsoon shifts."
    },
    "Manaus, Amazon Basin, Brazil": {
        "lat": -3.1190,
        "lon": -60.0210,
        "region": "South America",
        "biome": "Equatorial Rainforest",
        "significance": "Heart of the Amazon rainforest observing extreme hydrological cycles and heat stress."
    },
    "Longyearbyen, Svalbard (Arctic)": {
        "lat": 78.2232,
        "lon": 15.6469,
        "region": "Arctic High North",
        "biome": "Arctic Tundra / Permafrost",
        "significance": "One of the fastest-warming settlements on Earth experiencing polar amplification."
    },
    "Cape Town, South Africa": {
        "lat": -33.9249,
        "lon": 18.4241,
        "region": "Southern Africa",
        "biome": "Mediterranean Coastal",
        "significance": "Vulnerable coastal watershed famously impacted by the multi-year 'Day Zero' drought cycle."
    },
    "Furnace Creek, Death Valley, USA": {
        "lat": 36.4631,
        "lon": -116.8672,
        "region": "North America",
        "biome": "Hyper-arid Desert",
        "significance": "Global benchmark for extreme terrestrial heat and hyper-arid evaporative limits."
    },
    "Tokyo, Japan": {
        "lat": 35.6762,
        "lon": 139.6503,
        "region": "East Asia",
        "biome": "Urban Temperate Maritime",
        "significance": "Dense megalopolis showcasing urban heat island interactions with Pacific typhoon rainfall."
    },
    "London, United Kingdom": {
        "lat": 51.5074,
        "lon": -0.1278,
        "region": "Western Europe",
        "biome": "Temperate Oceanic",
        "significance": "Long-term Atlantic maritime climate record witnessing unprecedented heat extremes."
    },
    "Sydney, Australia": {
        "lat": -33.8688,
        "lon": 151.2093,
        "region": "Oceania",
        "biome": "Subtropical Coastal",
        "significance": "Subject to intense El Niño–Southern Oscillation (ENSO) rainfall and bushfire temperature swings."
    },
    "Tamanrasset, Sahara Desert, Algeria": {
        "lat": 22.7850,
        "lon": 5.5228,
        "region": "North Africa",
        "biome": "Subtropical Desert",
        "significance": "Core Saharan hyper-arid station monitoring continental desertification and dust dynamics."
    },
    "Summit Camp, Greenland Ice Sheet": {
        "lat": 72.5800,
        "lon": -38.4600,
        "region": "Greenland",
        "biome": "Continental Ice Sheet",
        "significance": "High-altitude ice cap observatory sensitive to surface albedo and summer melt incursions."
    }
}

# Default query settings
DEFAULT_LOCATION_KEY = "Nashik, Maharashtra, India (Featured)"
DEFAULT_START_YEAR = 2015
DEFAULT_END_YEAR = 2024
MIN_YEAR = 1985
MAX_YEAR = 2025

# Analysis thresholds
MIN_OBSERVATIONS_FOR_TREND = 60
SIGNIFICANCE_ALPHA = 0.05  # 95% confidence level
MIN_MONTH_DAYS_THRESHOLD = 20  # Minimum valid days in a month to compute monthly aggregate
