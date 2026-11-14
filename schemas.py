"""
Pydantic Request and Response Schemas
EarthScope Backend
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class LocationItem(BaseModel):
    id: str
    name: str
    short_name: str
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    region: str
    biome: str
    significance: str
    featured: bool = False

class LocationListResponse(BaseModel):
    total: int
    default_location_id: str
    locations: List[LocationItem]

class ClimateRecord(BaseModel):
    date: str  # YYYY-MM or YYYY-MM-DD
    year: int
    month: int
    t2m: Optional[float] = None
    t2m_max: Optional[float] = None
    t2m_min: Optional[float] = None
    prectotcorr: Optional[float] = None
    rh2m: Optional[float] = None
    ts: Optional[float] = None
    ws2m: Optional[float] = None
    source: str = "NASA POWER"

class ClimateSummary(BaseModel):
    mean_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    min_temperature: Optional[float] = None
    annual_precipitation: Optional[float] = None
    warmest_year: Optional[int] = None
    coldest_year: Optional[int] = None
    warmest_year_mean: Optional[float] = None
    wettest_year: Optional[int] = None
    total_records: int = 0
    valid_records: int = 0
    completeness_pct: float = 0.0

class ClimateResponse(BaseModel):
    status: str
    location_name: str
    latitude: float
    longitude: float
    temporal_resolution: str
    start_year: int
    end_year: int
    summary: ClimateSummary
    records: List[ClimateRecord]
    retrieval_metadata: Dict[str, Any]

class ClimateCompareItem(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    mean_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    total_records: int
    annual_series: List[Dict[str, Any]]

class ClimateCompareResponse(BaseModel):
    parameter: str
    parameter_name: str
    units: str
    period: str
    locations: List[ClimateCompareItem]

class TrendResult(BaseModel):
    parameter: str
    parameter_name: str
    units: str
    n_observations: int
    slope_per_year: Optional[float] = None
    slope_per_decade: Optional[float] = None
    intercept: Optional[float] = None
    r_squared: Optional[float] = None
    p_value: Optional[float] = None
    std_error: Optional[float] = None
    ci_95_lower: Optional[float] = None
    ci_95_upper: Optional[float] = None
    total_change_over_period: Optional[float] = None
    direction: str
    is_significant: bool
    mann_kendall_z: Optional[float] = None
    mann_kendall_p: Optional[float] = None
    sens_slope: Optional[float] = None
    verdict: str
    x_labels: List[str] = []
    y_actual: List[Optional[float]] = []
    y_fitted: List[Optional[float]] = []
    ci_lower_band: List[Optional[float]] = []
    ci_upper_band: List[Optional[float]] = []

class HistogramBin(BaseModel):
    bin_start: float
    bin_end: float
    label: str
    count: int

class DescriptiveStatistics(BaseModel):
    variable: str
    units: str
    total_records: int
    valid_observations: int
    missing_pct: float
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    q25: Optional[float] = None
    q75: Optional[float] = None
    iqr: Optional[float] = None
    p10: Optional[float] = None
    p90: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    histogram: List[HistogramBin] = []

class AnomalyRecord(BaseModel):
    date: str
    year: int
    month: int
    value: float
    baseline_mean: float
    baseline_std: float
    anomaly: float
    z_score: float
    is_extreme: bool
    insight: str

class AnomaliesResponse(BaseModel):
    variable: str
    units: str
    baseline_period: str
    total_months: int
    extreme_count: int
    threshold_z: float = 2.0
    all_anomalies: List[Dict[str, Any]]
    flagged_anomalies: List[AnomalyRecord]
    monthly_climatology: Dict[str, Dict[str, float]]

class ProjectionRecord(BaseModel):
    year: int
    value: Optional[float] = None
    projected_value: Optional[float] = None
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    type: str  # "historical" or "projected"

class ProjectionsResponse(BaseModel):
    variable: str
    units: str
    historical_start_year: int
    historical_end_year: int
    projected_horizon_years: int
    slope_per_year: Optional[float] = None
    r_squared: Optional[float] = None
    records: List[ProjectionRecord]
    methodology_disclaimer: str

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    nasa_power_reachable: bool
    cache_entries_count: int
    uptime_seconds: float
