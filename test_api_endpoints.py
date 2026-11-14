"""
Integration Tests for FastAPI Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["service"] == "EarthScope API"
    assert "version" in data
    assert "uptime_seconds" in data

def test_locations_endpoints():
    response = client.get("/api/locations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 10
    assert any(loc["id"] == "nashik" for loc in data["locations"])

    # Specific ID
    single_res = client.get("/api/locations/nashik")
    assert single_res.status_code == 200
    single_data = single_res.json()
    assert single_data["name"] == "Nashik, Maharashtra, India (Featured)"
    assert single_data["lat"] == 19.9975

def test_locations_404():
    response = client.get("/api/locations/non_existent_location_999")
    assert response.status_code == 404

def test_climate_validation_error():
    # start_year > end_year
    response = client.get("/api/climate?start_year=2024&end_year=2020")
    assert response.status_code == 400

    # invalid lat
    response_lat = client.get("/api/climate?lat=150.0")
    assert response_lat.status_code == 422
