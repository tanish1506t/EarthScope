# EarthScope — Earth System Trend Explorer
### NASA Space Apps Challenge 2026 | Challenge: *“Be An Earth System Trend Detective!”*
**Team:** CodeRex  
**Web & API Application URL:** `http://127.0.0.1:8000`

---

## 🛰️ 1. Project Overview & Scientific Motivation

**EarthScope — Earth System Trend Explorer** is an end-to-end, cinematic, full-stack 3D Earth science platform developed for the NASA Space Apps Challenge 2026. Inspired by NASA’s Earth-observing satellite fleet and the MERRA-2 modern reanalysis system, EarthScope enables students, researchers, educators, and citizens to investigate planetary environmental shifts with authentic data, rigorous statistics, and evidence-grounded insights.

Rather than presenting isolated temperature graphs or alarming headlines, EarthScope treats the user as an **Earth System Trend Detective**:
1. **Authentic Data Ingestion:** Direct integration with the NASA Langley Research Center (LaRC) POWER API v2 (modern reanalysis derived from GEOS FP-IT atmospheric models and satellite sounders).
2. **Quality-Controlled Filtering:** Strict missing-value quarantining (`-999.0` mapped to `NaN`) and physical boundary validation with zero synthetic data fabrication.
3. **Dual-Method Hypothesis Testing:** Parametric Ordinary Least Squares (OLS) with 95% Student's $t$ confidence intervals paired alongside non-parametric Mann-Kendall monotonic trend tests and Sen's slope median estimators.
4. **Physical Persistence & Autocorrelation:** Lag-1 autocorrelation ($r_1$) analysis and effective sample size ($N_{\text{eff}}$) corrections to prevent variance underestimation.
5. **Clear Attribution Boundaries:** Explicitly distinguishes empirical observations from causation, noting multi-decadal natural oscillations (ENSO, IOD, AMO) and spatial averaging vs microclimates.

---

## 🌟 2. Architecture & Modules

EarthScope features a **high-performance Python FastAPI backend** and a **cinematic 3D WebGL frontend**:

```
earthscope/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application, CORS, health & static mount
│   │   ├── config.py            # Parameters metadata, presets, and settings
│   │   ├── schemas.py           # Pydantic v2 validation models
│   │   ├── api/
│   │   │   ├── routes_locations.py  # /api/locations catalog
│   │   │   ├── routes_climate.py    # /api/climate & /api/climate/compare
│   │   │   ├── routes_analysis.py   # /api/analysis/{trends, statistics, anomalies, projections}
│   │   │   └── routes_reports.py    # /api/reports/{csv, pdf}
│   │   └── services/
│   │       ├── nasa_power.py        # NASA POWER API v2 client with TTL disk/memory cache
│   │       ├── climate_processing.py# Strict aggregation, NaN quarantining, and units
│   │       ├── statistics.py        # OLS regression, Mann-Kendall, Sen's slope
│   │       ├── anomaly_detection.py # Calendar-month baseline departures (|Z| > 2)
│   │       └── report_service.py    # CSV dossier and ReportLab PDF compilation
│   ├── tests/                   # Pytest automated test suite
│   ├── requirements.txt         # Backend dependencies
│   └── .env.example             # Environment variables
├── frontend/
│   ├── index.html               # 15-section cinematic single-page application
│   ├── css/style.css            # Deep-space glassmorphism visual identity
│   └── js/
│       ├── globe.js             # Three.js 3D Earth, atmosphere glow, clouds, 3D pins
│       ├── api.js               # Typed client connecting to FastAPI backend
│       └── app.js               # Application state, routing, Chart.js & Leaflet GIS
└── tests/                       # Additional algorithmic unit tests
```

---

## 🧭 3. 15 Complete Application Sections

1. **Home**: Cinematic Hero with rotating 3D Earth globe, live backend connection status badge, key indicators, and mission statement.
2. **Dashboard**: Executive climate indicators (Mean, Max, Min, Annual Precipitation, Completeness %) and dual time-series charts.
3. **Explore Earth 3D**: Fullscreen Three.js WebGL globe with planetary pins, interactive raycasting, fly-to camera controls, and mission HUD.
4. **Interactive Map**: Leaflet geospatial projection with CartoDB dark tiles, thermal sensor pins, and click-anywhere custom coordinate query.
5. **Temperature Analysis**: Diurnal thermal envelope bounded by nocturnal lows (`T2M_MIN`) and daytime highs (`T2M_MAX`).
6. **Rainfall Analysis**: Hydrological dynamics, monthly rainfall events, and 12-month climatological seasonal cycle.
7. **Climate Trends**: OLS linear regression with Student's $t$ confidence interval bands, $R^2$, and Mann-Kendall monotonic test verdict.
8. **Location Comparison**: Multi-location benchmark comparisons across diverse planetary biomes.
9. **Data Explorer**: Searchable and sortable table of verified NASA POWER observations with instant CSV export.
10. **Statistical Analysis**: Frequency distribution histogram, sample mean, median, standard deviation, IQR, skewness, and kurtosis.
11. **Anomaly Detection**: Calendar-month departures from normal, $|Z| > 2.0$ extreme event flags, and scientific insight generator.
12. **Trend Projections**: Empirical straight-line projections (1–10 years horizon) with prediction intervals and explicit attribution disclaimers.
13. **Reports & Exports**: Direct single-click export of verified CSV dossiers and publication-quality styled PDF reports.
14. **Data Sources & Methodology**: Exhaustive technical documentation of NASA POWER API v2 endpoints, parameters, and aggregation mathematics.
15. **About & Team**: NASA Space Apps Challenge 2026 challenge overview, problem statement, and Team CodeRex profile.

---

## 🛠️ 4. Technology Stack

- **Backend Framework:** Python 3.12+ / 3.14 with FastAPI 0.141+
- **ASGI Server:** Uvicorn 0.52+
- **HTTP Client:** HTTPX 0.28+ with dual-tier SHA-256 disk and memory TTL caching
- **Data & Math:** Pandas 3.0+, NumPy 2.5+, SciPy 1.18+
- **Data Validation:** Pydantic 2.13+
- **PDF Compilation:** ReportLab 5.1+
- **3D Hero Graphics:** Three.js r128 (WebGL rotating Earth, atmospheric glow shader, cloud layer, starfield, 3D pins)
- **Charts:** Chart.js 4.4+
- **Geospatial GIS:** Leaflet 1.9+ with CartoDB Dark Matter tiles
- **Test Automation:** Pytest 9.1+ (27 passing unit and integration tests)

---

## 🚀 5. Installation & Quickstart

### Prerequisites
- Python 3.10 to 3.14
- Git

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Launch FastAPI Server & Website
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser to:
- **Interactive Web Platform:** [`http://127.0.0.1:8000`](http://127.0.0.1:8000)
- **FastAPI OpenAPI Documentation:** [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
- **API Health & NASA POWER Ping:** [`http://127.0.0.1:8000/api/health`](http://127.0.0.1:8000/api/health)

---

## 🧪 6. Automated Unit Tests

Run the complete test suite across all services and endpoints:
```bash
python -m pytest tests/ backend/tests/ -v
```

All 27 automated tests verify:
- NASA POWER API response parsing and cache hashing
- Strict missing-value quarantining (`-999.0` mapped to `None`/`NaN`)
- Proper precipitation aggregation (`mm/day` rate converted to monthly accumulated `mm`)
- OLS linear regression, 95% confidence intervals, and Mann-Kendall rank tests
- Calendar-month climatology and $|Z| > 2.0$ extreme event detection
- CSV and PDF document generation
- FastAPI REST endpoints status codes and validation

---

## ⚖️ 7. Disclaimer & Acknowledgments

- **Challenge:** NASA Space Apps Challenge 2026: *“Be An Earth System Trend Detective!”*
- **Team:** CodeRex
- **Data Acknowledgments:** NASA Langley Research Center (LaRC) POWER Project and NASA Earth Science Division.
- **Disclaimer:** EarthScope is an independent educational and research project created by Team CodeRex for the NASA Space Apps Challenge. It is not an official product or endorsement of NASA.
