"""
Pages module for EarthScope
"""
from earthscope.pages.page_overview import render_overview_page
from earthscope.pages.page_temperature import render_temperature_page
from earthscope.pages.page_precipitation import render_precipitation_page
from earthscope.pages.page_vegetation import render_vegetation_page
from earthscope.pages.page_map import render_map_page
from earthscope.pages.page_trend_lab import render_trend_lab_page
from earthscope.pages.page_ai_insights import render_ai_insights_page
from earthscope.pages.page_methodology import render_methodology_page
from earthscope.pages.page_about import render_about_page
from earthscope.pages.page_gistemp import render_gistemp_page

__all__ = [
    "render_overview_page",
    "render_temperature_page",
    "render_precipitation_page",
    "render_vegetation_page",
    "render_gistemp_page",
    "render_map_page",
    "render_trend_lab_page",
    "render_ai_insights_page",
    "render_methodology_page",
    "render_about_page"
]
