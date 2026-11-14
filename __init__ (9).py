"""
Visualizations module for EarthScope
"""
from earthscope.visualizations.charts import (
    plot_timeseries_with_trend,
    plot_temperature_envelope,
    plot_precipitation_analysis,
    plot_monthly_climatology,
    plot_monthly_anomalies,
    plot_distribution_histogram
)
from earthscope.visualizations.maps import create_global_earth_map

__all__ = [
    "plot_timeseries_with_trend",
    "plot_temperature_envelope",
    "plot_precipitation_analysis",
    "plot_monthly_climatology",
    "plot_monthly_anomalies",
    "plot_distribution_histogram",
    "create_global_earth_map"
]
