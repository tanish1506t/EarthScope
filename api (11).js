/**
 * EarthScope API Client
 * Connects Frontend directly to Python FastAPI NASA POWER Backend
 * NASA Space Apps Challenge 2026 | Team CodeRex
 */

class EarthScopeApiClient {
  constructor() {
    // Automatically determine whether to use absolute or relative base URL
    const isLocalFile = window.location.protocol === 'file:';
    this.baseUrl = window.EARTHSCOPE_API_BASE || (isLocalFile ? 'http://127.0.0.1:8000' : '');
  }

  async _fetch(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        let errDetail = `HTTP ${response.status} ${response.statusText}`;
        try {
          const errJson = await response.json();
          if (errJson.detail) errDetail = errJson.detail;
        } catch (_) {}
        throw new Error(errDetail);
      }
      return await response.json();
    } catch (error) {
      console.warn(`API call failed for [${endpoint}]:`, error);
      throw error;
    }
  }

  async checkHealth() {
    return this._fetch('/api/health');
  }

  async getLocations() {
    return this._fetch('/api/locations');
  }

  async getClimateData(lat, lon, startYear = 2015, endYear = 2024, parameters = null, forceRefresh = false) {
    const params = new URLSearchParams({
      lat: lat.toFixed(4),
      lon: lon.toFixed(4),
      start_year: startYear,
      end_year: endYear,
      force_refresh: forceRefresh
    });
    if (parameters) {
      params.append('parameters', parameters);
    }
    return this._fetch(`/api/climate?${params.toString()}`);
  }

  async compareLocations(parameter = 't2m', locationIds = null, startYear = 2015, endYear = 2024) {
    const params = new URLSearchParams({
      parameter: parameter,
      start_year: startYear,
      end_year: endYear
    });
    if (locationIds) {
      params.append('location_ids', locationIds);
    }
    return this._fetch(`/api/climate/compare?${params.toString()}`);
  }

  async getTrends(lat, lon, startYear = 2015, endYear = 2024, parameter = 't2m', temporalGroup = 'yearly') {
    const params = new URLSearchParams({
      lat: lat.toFixed(4),
      lon: lon.toFixed(4),
      start_year: startYear,
      end_year: endYear,
      parameter: parameter,
      temporal_group: temporalGroup
    });
    return this._fetch(`/api/analysis/trends?${params.toString()}`);
  }

  async getStatistics(lat, lon, startYear = 2015, endYear = 2024, parameter = 't2m') {
    const params = new URLSearchParams({
      lat: lat.toFixed(4),
      lon: lon.toFixed(4),
      start_year: startYear,
      end_year: endYear,
      parameter: parameter
    });
    return this._fetch(`/api/analysis/statistics?${params.toString()}`);
  }

  async getAnomalies(lat, lon, startYear = 2015, endYear = 2024, parameter = 't2m') {
    const params = new URLSearchParams({
      lat: lat.toFixed(4),
      lon: lon.toFixed(4),
      start_year: startYear,
      end_year: endYear,
      parameter: parameter
    });
    return this._fetch(`/api/analysis/anomalies?${params.toString()}`);
  }

  async getProjections(lat, lon, startYear = 2015, endYear = 2024, parameter = 't2m', horizonYears = 5) {
    const params = new URLSearchParams({
      lat: lat.toFixed(4),
      lon: lon.toFixed(4),
      start_year: startYear,
      end_year: endYear,
      parameter: parameter,
      horizon_years: horizonYears
    });
    return this._fetch(`/api/analysis/projections?${params.toString()}`);
  }

  getReportDownloadUrl(type, lat, lon, startYear, endYear, locationName) {
    const params = new URLSearchParams({
      lat: lat.toFixed(4),
      lon: lon.toFixed(4),
      start_year: startYear,
      end_year: endYear,
      location_name: locationName || ''
    });
    return `${this.baseUrl}/api/reports/${type}?${params.toString()}`;
  }

  async downloadCSV(lat, lon, startYear, endYear, locationName) {
    const url = this.getReportDownloadUrl('csv', lat, lon, startYear, endYear, locationName);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `earthscope_data_${startYear}_${endYear}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  async downloadPDF(lat, lon, startYear, endYear, locationName) {
    const url = this.getReportDownloadUrl('pdf', lat, lon, startYear, endYear, locationName);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `earthscope_report_${startYear}_${endYear}.pdf`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

window.earthScopeApi = new EarthScopeApiClient();
