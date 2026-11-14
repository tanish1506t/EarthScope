"""
EarthScope FastAPI Main Application
NASA Space Apps Challenge 2026 | Team CodeRex
"""

import time
import os
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import settings
from backend.app.schemas import HealthResponse
from backend.app.services.nasa_power import nasa_service
from backend.app.api import routes_locations, routes_climate, routes_analysis, routes_reports

START_TIME = time.time()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(routes_locations.router)
app.include_router(routes_climate.router)
app.include_router(routes_analysis.router)
app.include_router(routes_reports.router)

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Returns API health status, NASA POWER upstream reachability, cache stats, and uptime.
    """
    nasa_ok = await nasa_service.check_api_health()
    uptime = time.time() - START_TIME
    return HealthResponse(
        status="ok" if nasa_ok else "degraded",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        nasa_power_reachable=nasa_ok,
        cache_entries_count=nasa_service.get_cache_count(),
        uptime_seconds=round(uptime, 2)
    )

# Static files / Frontend mounting
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")
if os.path.exists(FRONTEND_DIR):
    css_dir = os.path.join(FRONTEND_DIR, "css")
    js_dir = os.path.join(FRONTEND_DIR, "js")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "EarthScope API is running. Frontend index.html not found."}
else:
    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/api/health"
        }
