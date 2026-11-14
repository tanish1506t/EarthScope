/**
 * EarthScope Main Application Controller
 * Handles Navigation, State, Backend Synchronization, Chart.js Visualizations & Leaflet Map
 * NASA Space Apps Challenge 2026 | Team CodeRex
 */

// Application State Store
const state = {
  activePage: 'home',
  activeLocation: {
    id: 'nashik',
    name: 'Nashik, Maharashtra, India (Featured)',
    short_name: 'Nashik, India',
    lat: 19.9975,
    lon: 73.7898,
    region: 'South Asia',
    biome: 'Tropical Wet-and-Dry / Viticulture Hub',
    significance: 'Crucial viticultural and agricultural basin with seasonal South Asian monsoon shifts.',
    featured: true
  },
  locations: [],
  startYear: 2015,
  endYear: 2024,
  climateData: null,
  trendData: null,
  statsData: null,
  anomData: null,
  projData: null,
  isLoading: false,
  backendConnected: false,
  heroGlobe: null,
  exploreGlobe: null,
  leafletMap: null,
  mapMarkers: []
};

// Registered Chart.js instances cache
const charts = {};

// Safe number formatter
const fmt = (val, decimals = 1) => {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return Number(val).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
};

// Dynamic Count-Up Animation for UI metrics
function animateNumber(elementId, targetValue, suffix = '', decimals = 1, duration = 800) {
  const el = document.getElementById(elementId);
  if (!el) return;
  if (targetValue === null || targetValue === undefined || isNaN(targetValue)) {
    el.textContent = '—';
    return;
  }
  const target = Number(targetValue);
  const start = 0;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    // Smooth ease-out cubic
    const easeProgress = 1 - Math.pow(1 - progress, 3);
    const current = start + (target - start) * easeProgress;
    el.textContent = `${fmt(current, decimals)}${suffix}`;
    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }
  requestAnimationFrame(update);
}

// UI Notification Toast
function showToast(message, isError = false) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.innerHTML = `<span style="font-size:16px;">${isError ? '⚠️' : '🛰️'}</span> <span>${message}</span>`;
  toast.style.borderColor = isError ? 'var(--red)' : 'var(--cyan)';
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3800);
}

// Chart.js Helper: safely destroy existing chart before creating a new one
function renderChart(id, type, labels, datasets, extraOptions = {}) {
  const canvas = document.getElementById(id);
  if (!canvas) return;

  if (charts[id]) {
    charts[id].destroy();
  }

  const textColor = '#94a3b8';
  const gridColor = 'rgba(255, 255, 255, 0.08)';

  const defaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: '#e2e8f0', font: { family: 'Inter', size: 11 }, boxWidth: 12 }
      },
      tooltip: {
        backgroundColor: 'rgba(6, 13, 31, 0.9)',
        borderColor: 'rgba(56, 189, 248, 0.3)',
        borderWidth: 1,
        titleColor: '#00f0ff',
        bodyColor: '#f1f5f9',
        padding: 10
      }
    },
    scales: {
      x: {
        ticks: { color: textColor, font: { size: 10 }, maxTicksLimit: 14 },
        grid: { color: gridColor }
      },
      y: {
        ticks: { color: textColor, font: { size: 10 } },
        grid: { color: gridColor }
      }
    }
  };

  const mergedOptions = Object.assign({}, defaultOptions, extraOptions);
  charts[id] = new Chart(canvas, {
    type: type,
    data: {
      labels: labels,
      datasets: datasets.map(ds => Object.assign({
        borderWidth: 2,
        pointRadius: 2,
        tension: 0.25
      }, ds))
    },
    options: mergedOptions
  });
}

// Page Routing & Navigation
function navigateTo(pageId) {
  state.activePage = pageId;

  // Toggle pages
  document.querySelectorAll('.page-view').forEach(p => {
    p.classList.toggle('active', p.id === `page-${pageId}`);
  });

  // Toggle sidebar active states
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.page === pageId);
  });

  // Update top bar title
  const titleMap = {
    home: ['Home', 'Discover Earth’s changing climate through NASA observation data.'],
    dash: ['Overview Dashboard', 'Key planetary metrics, temperature, and precipitation trends.'],
    globe: ['Explore 3D Earth', 'Interactive rotating WebGL globe with planetary coordinate pinning.'],
    map: ['Interactive Geospatial Map', 'Leaflet global projection with thermal sensor overlays.'],
    temp: ['Temperature Analysis', 'Monthly to decadal thermal envelopes and diurnal swings.'],
    rain: ['Precipitation & Hydrology', 'Rainfall event dynamics, dry spells, and seasonal monsoon cycles.'],
    trend: ['Climate Trends & Hypotheses', 'OLS linear regression and Mann-Kendall monotonic test.'],
    comp: ['Location Comparison', 'Side-by-side benchmark comparison across diverse global biomes.'],
    explore: ['Data Explorer', 'Searchable, filterable historical NASA POWER records table.'],
    stats: ['Statistical Analytics', 'Frequency distribution histograms and summary metrics.'],
    anom: ['Anomaly Detection', 'Calendar-month departures and statistically extreme (|Z| > 2) flags.'],
    pred: ['Trend Projections', 'Empirical regression projections with explicit scientific caveats.'],
    rep: ['Reports & Exports', 'Generate and download verified CSV dossiers and publication PDFs.'],
    src: ['Data Sources & Methodology', 'NASA POWER API v2 endpoints, physical parameters, and equations.'],
    about: ['About & Team', 'NASA Space Apps Challenge 2026 | Team CodeRex']
  };

  if (titleMap[pageId]) {
    document.getElementById('header-title').textContent = titleMap[pageId][0];
    document.getElementById('header-subtitle').textContent = titleMap[pageId][1];
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Sound and 3D card physics trigger
  if (window.SoundFX) window.SoundFX.playClick();
  setTimeout(initCard3DTilt, 60);

  // Page-specific initialization triggers
  if (pageId === 'globe' && !state.exploreGlobe) {
    initExploreGlobe();
  } else if (pageId === 'globe' && state.exploreGlobe) {
    state.exploreGlobe.onWindowResize();
  }

  if (pageId === 'map') {
    setTimeout(() => initLeafletMap(), 150);
  }

  renderActivePage();
}

// Fetch climate data for currently active location and update all views
async function loadActiveLocationData() {
  setLoadingState(true);
  try {
    const loc = state.activeLocation;
    const climate = await earthScopeApi.getClimateData(loc.lat, loc.lon, state.startYear, state.endYear);
    state.climateData = climate;

    // Concurrently fetch analysis results
    const [trends, stats, anoms, projs] = await Promise.all([
      earthScopeApi.getTrends(loc.lat, loc.lon, state.startYear, state.endYear),
      earthScopeApi.getStatistics(loc.lat, loc.lon, state.startYear, state.endYear),
      earthScopeApi.getAnomalies(loc.lat, loc.lon, state.startYear, state.endYear),
      earthScopeApi.getProjections(loc.lat, loc.lon, state.startYear, state.endYear)
    ]);

    state.trendData = trends;
    state.statsData = stats;
    state.anomData = anoms;
    state.projData = projs;

    updateHeaderLocationDisplay();
    renderActivePage();
    if (window.SoundFX) window.SoundFX.playSuccess();
    setTimeout(initCard3DTilt, 60);
  } catch (error) {
    showToast(`Failed to load data for ${state.activeLocation.short_name}: ${error.message}`, true);
  } finally {
    setLoadingState(false);
  }
}

function setLoadingState(isLoading) {
  state.isLoading = isLoading;
  const statusEl = document.getElementById('backend-status-text');
  const dotEl = document.getElementById('backend-status-dot');
  if (isLoading) {
    if (statusEl) statusEl.textContent = `Syncing NASA POWER data (${state.activeLocation.short_name})...`;
    if (dotEl) dotEl.className = 'status-dot degraded';
  } else {
    if (statusEl) statusEl.textContent = `Live NASA POWER API · ${state.activeLocation.short_name}`;
    if (dotEl) dotEl.className = 'status-dot';
  }
}

function updateHeaderLocationDisplay() {
  const sel = document.getElementById('global-location-select');
  if (sel && state.activeLocation) {
    sel.value = state.activeLocation.id;
  }
  const heroLoc = document.getElementById('hero-active-location');
  if (heroLoc && state.activeLocation) {
    heroLoc.textContent = state.activeLocation.name;
  }
}

// Select location by ID
function selectLocation(locationId) {
  const found = state.locations.find(l => l.id.toLowerCase() === locationId.toLowerCase());
  if (found) {
    state.activeLocation = found;
    updateHeaderLocationDisplay();
    if (state.heroGlobe) {
      state.heroGlobe.flyToLocation(found.lat, found.lon);
    }
    if (state.exploreGlobe) {
      state.exploreGlobe.flyToLocation(found.lat, found.lon);
    }
    if (state.leafletMap) {
      state.leafletMap.flyTo([found.lat, found.lon], 5);
    }
    loadActiveLocationData();
    showToast(`Loaded ${found.short_name} (${found.lat.toFixed(2)}°, ${found.lon.toFixed(2)}°)`);
  }
}

// Render active page view content
function renderActivePage() {
  if (!state.climateData) return;

  switch (state.activePage) {
    case 'home':
      renderHomePage();
      break;
    case 'dash':
      renderDashboardPage();
      break;
    case 'globe':
      renderGlobePage();
      break;
    case 'map':
      renderMapPage();
      break;
    case 'temp':
      renderTemperaturePage();
      break;
    case 'rain':
      renderRainfallPage();
      break;
    case 'trend':
      renderTrendsPage();
      break;
    case 'comp':
      renderComparisonPage();
      break;
    case 'explore':
      renderExplorerPage();
      break;
    case 'stats':
      renderStatisticsPage();
      break;
    case 'anom':
      renderAnomaliesPage();
      break;
    case 'pred':
      renderProjectionsPage();
      break;
    case 'rep':
      renderReportsPage();
      break;
  }
}

/* ==========================================================================
   PAGE RENDERERS
   ========================================================================== */

function renderHomePage() {
  const summ = state.climateData.summary;
  animateNumber('hero-m-temp', summ.mean_temperature, ' °C', 1);
  animateNumber('hero-m-rain', summ.annual_precipitation, ' mm', 0);
  document.getElementById('hero-m-warmest').textContent = summ.warmest_year || '—';
  document.getElementById('hero-m-records').textContent = `${summ.valid_records} / ${summ.total_records}`;
}

function renderDashboardPage() {
  const summ = state.climateData.summary;
  const recs = state.climateData.records;

  animateNumber('dash-m-avg-temp', summ.mean_temperature, ' °C', 1);
  animateNumber('dash-m-max-temp', summ.max_temperature, ' °C', 1);
  animateNumber('dash-m-min-temp', summ.min_temperature, ' °C', 1);
  animateNumber('dash-m-rain', summ.annual_precipitation, ' mm', 0);
  document.getElementById('dash-m-records').textContent = `${summ.valid_records} records (${summ.completeness_pct}%)`;

  // Temperature line chart
  const dates = recs.map(r => r.date);
  const tVals = recs.map(r => r.t2m);
  renderChart('chart-dash-temp', 'line', dates, [{
    label: 'Mean Temperature (°C)',
    data: tVals,
    borderColor: '#00f0ff',
    backgroundColor: 'rgba(0, 240, 255, 0.1)',
    fill: true
  }]);

  // Precipitation bar chart
  const rVals = recs.map(r => r.prectotcorr);
  renderChart('chart-dash-rain', 'bar', dates, [{
    label: 'Rainfall (mm)',
    data: rVals,
    backgroundColor: '#3b82f6',
    borderRadius: 3
  }]);
}

function renderGlobePage() {
  const loc = state.activeLocation;
  const summ = state.climateData.summary;

  document.getElementById('globe-hud-loc-name').textContent = loc.name;
  document.getElementById('globe-hud-coords').textContent = `${loc.lat.toFixed(4)}° N, ${loc.lon.toFixed(4)}° E`;
  document.getElementById('globe-hud-biome').textContent = loc.biome;
  document.getElementById('globe-hud-stats').innerHTML = `
    Mean Temperature: <b style="color:var(--cyan)">${fmt(summ.mean_temperature)} °C</b><br/>
    Annual Rainfall: <b style="color:var(--cyan-bright)">${fmt(summ.annual_precipitation, 0)} mm</b><br/>
    Warmest Year: <b style="color:var(--amber)">${summ.warmest_year || '—'}</b>
  `;

  // Render location selector chips
  const chipsContainer = document.getElementById('globe-location-chips');
  if (chipsContainer) {
    chipsContainer.innerHTML = state.locations.map(l => `
      <button class="chip ${l.id === loc.id ? 'active' : ''}" onclick="selectLocation('${l.id}')">
        ${l.short_name}
      </button>
    `).join('');
  }
}

function renderMapPage() {
  const loc = state.activeLocation;
  const summ = state.climateData.summary;
  document.getElementById('map-hud-info').innerHTML = `
    <strong>Target Location:</strong> ${loc.name} (${loc.lat.toFixed(4)}°, ${loc.lon.toFixed(4)}°)<br/>
    <strong>Biome / Setting:</strong> ${loc.biome}<br/>
    <strong>Mean Temperature:</strong> ${fmt(summ.mean_temperature)} °C · <strong>Annual Rainfall:</strong> ${fmt(summ.annual_precipitation, 0)} mm
  `;
}

function renderTemperaturePage() {
  const recs = state.climateData.records;
  const dates = recs.map(r => r.date);

  renderChart('chart-temp-main', 'line', dates, [
    {
      label: 'Max Temp (°C)',
      data: recs.map(r => r.t2m_max),
      borderColor: '#f43f5e',
      borderDash: [3, 3],
      pointRadius: 1
    },
    {
      label: 'Mean Temp (°C)',
      data: recs.map(r => r.t2m),
      borderColor: '#00f0ff',
      backgroundColor: 'rgba(0, 240, 255, 0.12)',
      fill: true
    },
    {
      label: 'Min Temp (°C)',
      data: recs.map(r => r.t2m_min),
      borderColor: '#38bdf8',
      borderDash: [3, 3],
      pointRadius: 1
    }
  ]);

  if (state.statsData) {
    const s = state.statsData;
    document.getElementById('temp-stats-metrics').innerHTML = `
      <div class="metric-card"><div class="metric-label">Mean Temperature</div><div class="metric-val cyan">${fmt(s.mean)} °C</div></div>
      <div class="metric-card"><div class="metric-label">Median Temperature</div><div class="metric-val blue">${fmt(s.median)} °C</div></div>
      <div class="metric-card"><div class="metric-label">Standard Deviation</div><div class="metric-val purple">${fmt(s.std)} °C</div></div>
      <div class="metric-card"><div class="metric-label">Range (Min / Max)</div><div class="metric-val amber">${fmt(s.min)} / ${fmt(s.max)} °C</div></div>
    `;
  }
}

function renderRainfallPage() {
  const recs = state.climateData.records;
  const dates = recs.map(r => r.date);

  renderChart('chart-rain-monthly', 'bar', dates, [{
    label: 'Monthly Precipitation (mm)',
    data: recs.map(r => r.prectotcorr),
    backgroundColor: '#3b82f6',
    borderRadius: 3
  }]);

  // Seasonal calendar month averages (Jan - Dec)
  if (state.anomData && state.anomData.monthly_climatology) {
    const cl = state.anomData.monthly_climatology;
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthMeans = Object.keys(cl).sort().map(k => cl[k].mean);

    renderChart('chart-rain-seasonal', 'bar', monthNames, [{
      label: 'Climatological Mean (°C / Reference Cycle)',
      data: monthMeans,
      backgroundColor: '#a855f7',
      borderRadius: 4
    }]);
  }
}

function renderTrendsPage() {
  if (!state.trendData) return;
  const t = state.trendData;

  renderChart('chart-trend-regression', 'line', t.x_labels, [
    {
      label: 'Observed Annual Value',
      data: t.y_actual,
      borderColor: '#00f0ff',
      pointRadius: 3
    },
    {
      label: 'OLS Fitted Trend Line',
      data: t.y_fitted,
      borderColor: '#f59e0b',
      borderDash: [5, 4],
      pointRadius: 0
    },
    {
      label: '95% Confidence Upper Band',
      data: t.ci_upper_band,
      borderColor: 'rgba(245, 158, 11, 0.35)',
      borderDash: [2, 2],
      pointRadius: 0
    },
    {
      label: '95% Confidence Lower Band',
      data: t.ci_lower_band,
      borderColor: 'rgba(245, 158, 11, 0.35)',
      borderDash: [2, 2],
      pointRadius: 0
    }
  ]);

  document.getElementById('trend-slope-display').textContent = `${t.slope_per_decade > 0 ? '+' : ''}${fmt(t.slope_per_decade, 3)} °C / decade`;
  document.getElementById('trend-r2-display').textContent = fmt(t.r_squared, 3);
  document.getElementById('trend-p-display').textContent = fmt(t.p_value, 4);
  document.getElementById('trend-mk-display').textContent = `Z = ${fmt(t.mann_kendall_z, 2)} (Sen's Slope: ${fmt(t.sens_slope, 4)})`;
  document.getElementById('trend-verdict-text').textContent = t.verdict;
}

async function renderComparisonPage() {
  const param = document.getElementById('comp-param-select')?.value || 't2m';
  try {
    const comp = await earthScopeApi.compareLocations(param);
    const locNames = comp.locations.map(l => l.location_name);
    const meanVals = comp.locations.map(l => l.mean_value);

    renderChart('chart-comp-locations', 'bar', locNames, [{
      label: `${comp.parameter_name} (${comp.units})`,
      data: meanVals,
      backgroundColor: '#a855f7',
      borderRadius: 4
    }]);

    // Comparison Table
    const tbody = document.getElementById('comp-table-body');
    if (tbody) {
      tbody.innerHTML = comp.locations.map(l => `
        <tr>
          <td><strong>${l.location_name}</strong></td>
          <td>${l.latitude.toFixed(2)}°, ${l.longitude.toFixed(2)}°</td>
          <td><b style="color:var(--cyan)">${fmt(l.mean_value)} ${comp.units}</b></td>
          <td>${fmt(l.min_value)} ${comp.units}</td>
          <td>${fmt(l.max_value)} ${comp.units}</td>
          <td>${l.total_records}</td>
        </tr>
      `).join('');
    }
  } catch (e) {
    console.error('Comparison error:', e);
  }
}

function renderExplorerPage() {
  const recs = state.climateData.records;
  const tbody = document.getElementById('explorer-table-body');
  if (!tbody) return;

  const searchTerm = (document.getElementById('explorer-search-input')?.value || '').toLowerCase();
  const filtered = recs.filter(r => r.date.includes(searchTerm));

  tbody.innerHTML = filtered.slice(0, 150).map(r => `
    <tr>
      <td><strong>${r.date}</strong></td>
      <td>${state.activeLocation.short_name}</td>
      <td><b style="color:var(--cyan)">${fmt(r.t2m)}</b></td>
      <td>${fmt(r.t2m_max)}</td>
      <td>${fmt(r.t2m_min)}</td>
      <td>${fmt(r.prectotcorr)}</td>
      <td>${fmt(r.rh2m)}</td>
      <td>${r.source}</td>
    </tr>
  `).join('') || `<tr><td colspan="8" style="text-align:center;padding:24px;color:var(--text-muted)">No matching records found.</td></tr>`;
}

function renderStatisticsPage() {
  if (!state.statsData) return;
  const s = state.statsData;

  document.getElementById('stats-m-mean').textContent = `${fmt(s.mean)} ${s.units}`;
  document.getElementById('stats-m-median').textContent = `${fmt(s.median)} ${s.units}`;
  document.getElementById('stats-m-std').textContent = `${fmt(s.std)} ${s.units}`;
  document.getElementById('stats-m-skewness').textContent = fmt(s.skewness, 3);
  document.getElementById('stats-m-iqr').textContent = `${fmt(s.iqr)} ${s.units}`;
  document.getElementById('stats-m-minmax').textContent = `${fmt(s.min)} / ${fmt(s.max)} ${s.units}`;

  if (s.histogram && s.histogram.length > 0) {
    renderChart('chart-stats-hist', 'bar', s.histogram.map(b => b.label), [{
      label: 'Observation Frequency (Months)',
      data: s.histogram.map(b => b.count),
      backgroundColor: '#3b82f6',
      borderRadius: 4
    }]);
  }
}

function renderAnomaliesPage() {
  if (!state.anomData) return;
  const a = state.anomData;

  const dates = a.all_anomalies.map(r => r.date);
  const anomVals = a.all_anomalies.map(r => r.anomaly);
  const bgColors = anomVals.map(v => v >= 0 ? '#f43f5e' : '#38bdf8');

  renderChart('chart-anom-diverging', 'bar', dates, [{
    label: 'Temperature Anomaly (°C)',
    data: anomVals,
    backgroundColor: bgColors,
    borderRadius: 2
  }]);

  const tbody = document.getElementById('anomalies-table-body');
  if (tbody) {
    if (a.flagged_anomalies.length > 0) {
      tbody.innerHTML = a.flagged_anomalies.map(f => `
        <tr>
          <td><strong>${f.date}</strong></td>
          <td>${fmt(f.value)} °C</td>
          <td>${fmt(f.baseline_mean)} °C</td>
          <td><b style="color:${f.anomaly > 0 ? 'var(--red)' : 'var(--cyan)'}">${f.anomaly > 0 ? '+' : ''}${fmt(f.anomaly, 2)} °C</b></td>
          <td><span class="badge-extreme">Z = ${f.z_score > 0 ? '+' : ''}${fmt(f.z_score, 2)}</span></td>
          <td>${f.insight}</td>
        </tr>
      `).join('');
    } else {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--text-muted)">No monthly anomalies exceeded the strict |Z| > 2.0 standard deviation threshold over this period.</td></tr>`;
    }
  }
}

function renderProjectionsPage() {
  if (!state.projData) return;
  const p = state.projData;

  const labels = p.records.map(r => String(r.year));
  const histVals = p.records.map(r => r.type === 'historical' ? r.value : null);
  const projVals = p.records.map(r => r.projected_value);
  const ciLower = p.records.map(r => r.ci_lower);
  const ciUpper = p.records.map(r => r.ci_upper);

  renderChart('chart-proj-future', 'line', labels, [
    {
      label: 'Historical Observations',
      data: histVals,
      borderColor: '#00f0ff',
      pointRadius: 3
    },
    {
      label: 'Empirical Linear Trend',
      data: projVals,
      borderColor: '#f59e0b',
      borderDash: [5, 4],
      pointRadius: 2
    },
    {
      label: 'Projection Upper Limit (95% PI)',
      data: ciUpper,
      borderColor: 'rgba(245, 158, 11, 0.4)',
      borderDash: [2, 2],
      pointRadius: 0
    },
    {
      label: 'Projection Lower Limit (95% PI)',
      data: ciLower,
      borderColor: 'rgba(245, 158, 11, 0.4)',
      borderDash: [2, 2],
      pointRadius: 0
    }
  ]);

  document.getElementById('proj-disclaimer-text').textContent = p.methodology_disclaimer;
}

function renderReportsPage() {
  const loc = state.activeLocation;
  const summ = state.climateData.summary;
  const trend = state.trendData;

  document.getElementById('report-summary-box').innerHTML = `
    <h4 style="color:#ffffff;margin-bottom:8px;">Scientific Investigation Dossier: ${loc.name}</h4>
    <p style="font-size:13px;line-height:1.7;color:var(--text-muted);">
      Analysis window: <strong>${state.startYear} to ${state.endYear}</strong> (${summ.valid_records} validated observations).<br/>
      Baseline Mean Air Temperature: <strong>${fmt(summ.mean_temperature)} °C</strong> (Recorded Max: ${fmt(summ.max_temperature)} °C, Min: ${fmt(summ.min_temperature)} °C).<br/>
      Average Annual Precipitation: <strong>${fmt(summ.annual_precipitation, 0)} mm / year</strong>.<br/>
      OLS Historical Trend: <strong>${trend ? fmt(trend.slope_per_decade, 3) : '—'} °C / decade</strong> (Mann-Kendall: ${trend ? trend.verdict : '—'}).<br/>
      Primary Observation Source: <strong>NASA Langley Research Center POWER Project v2</strong>.
    </p>
  `;
}

/* ==========================================================================
   INITIALIZATION & MAPS
   ========================================================================== */

function initExploreGlobe() {
  state.exploreGlobe = new EarthScopeGlobe('full-globe-canvas', {
    radius: 110,
    autoRotate: true,
    interactive: true,
    onLocationSelect: (loc) => selectLocation(loc.id)
  });
  state.exploreGlobe.setLocations(state.locations);
  state.exploreGlobe.flyToLocation(state.activeLocation.lat, state.activeLocation.lon);
}

function initLeafletMap() {
  if (state.leafletMap) return;

  const mapContainer = document.getElementById('leaflet-map');
  if (!mapContainer || typeof L === 'undefined') return;

  state.leafletMap = L.map('leaflet-map', {
    zoomControl: true,
    minZoom: 2,
    maxZoom: 10
  }).setView([state.activeLocation.lat, state.activeLocation.lon], 4);

  // CartoDB Dark Matter Tiles (CORS-friendly, dark aesthetic)
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(state.leafletMap);

  // Add markers for all benchmark locations
  state.locations.forEach(loc => {
    const isCurrent = loc.id === state.activeLocation.id;
    const marker = L.circleMarker([loc.lat, loc.lon], {
      radius: isCurrent ? 9 : 6,
      fillColor: isCurrent ? '#00f0ff' : '#38bdf8',
      color: '#ffffff',
      weight: isCurrent ? 2.5 : 1,
      opacity: 1,
      fillOpacity: 0.85
    }).addTo(state.leafletMap);

    marker.bindPopup(`
      <div style="font-family:Inter,sans-serif;color:#0b172a;font-size:12px;padding:4px;">
        <b style="font-size:13px;">${loc.name}</b><br/>
        <span>${loc.biome}</span><br/>
        <button style="margin-top:6px;padding:4px 8px;background:#00f0ff;border:none;border-radius:4px;cursor:pointer;font-weight:700;" onclick="selectLocation('${loc.id}')">Analyze Location →</button>
      </div>
    `);

    marker.on('click', () => {
      selectLocation(loc.id);
    });

    state.mapMarkers.push(marker);
  });

  // Support clicking anywhere on map to analyze custom coordinates!
  state.leafletMap.on('click', (e) => {
    const customLat = e.latlng.lat;
    const customLon = e.latlng.lng;
    state.activeLocation = {
      id: `custom_${customLat.toFixed(2)}_${customLon.toFixed(2)}`,
      name: `Custom Location (${customLat.toFixed(2)}°, ${customLon.toFixed(2)}°)`,
      short_name: `Point (${customLat.toFixed(1)}°, ${customLon.toFixed(1)}°)`,
      lat: customLat,
      lon: customLon,
      region: 'Custom Query',
      biome: 'Targeted Geospatial Coordinate',
      significance: 'User-specified coordinates queried directly against NASA POWER.',
      featured: false
    };
    updateHeaderLocationDisplay();
    loadActiveLocationData();
    showToast(`Investigating custom coordinates: ${customLat.toFixed(2)}°, ${customLon.toFixed(2)}°`);
  });
}

// Background Starfield Canvas Animation
function initBackgroundCanvas() {
  const canvas = document.getElementById('space-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  const stars = [];
  for (let i = 0; i < 180; i++) {
    stars.push({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      radius: Math.random() * 1.5,
      alpha: 0.2 + Math.random() * 0.8,
      speed: 0.1 + Math.random() * 0.4
    });
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    stars.forEach(s => {
      ctx.fillStyle = `rgba(0, 240, 255, ${s.alpha * 0.6})`;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
      ctx.fill();

      s.y -= s.speed;
      if (s.y < 0) s.y = canvas.height;
    });
    requestAnimationFrame(draw);
  }
  draw();
}

// Sci-Fi Web Audio API Synthesizer (Zero external audio files required)
const SoundFX = {
  ctx: null,
  enabled: true,

  init() {
    if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    }
  },

  play(freq = 880, duration = 0.08, type = 'sine', gainVal = 0.04) {
    if (!this.enabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      if (this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      gain.gain.setValueAtTime(gainVal, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch (e) {
      // Autoplay policy fallback
    }
  },

  playClick() {
    this.play(1040, 0.04, 'triangle', 0.035);
  },

  playSwitch() {
    this.play(840, 0.05, 'sine', 0.04);
    setTimeout(() => this.play(1260, 0.06, 'sine', 0.03), 40);
  },

  playSuccess() {
    const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
    notes.forEach((f, i) => {
      setTimeout(() => this.play(f, 0.1, 'sine', 0.03), i * 50);
    });
  },

  playToggle() {
    this.enabled = !this.enabled;
    const btn = document.getElementById('sfx-toggle-btn');
    if (btn) {
      btn.innerHTML = this.enabled ? '🔊 SFX <span style="color:var(--cyan)">ON</span>' : '🔇 SFX OFF';
      btn.style.borderColor = this.enabled ? 'rgba(0, 240, 255, 0.4)' : 'rgba(255, 255, 255, 0.1)';
    }
    if (this.enabled) this.playSuccess();
    return this.enabled;
  }
};
window.SoundFX = SoundFX;

// Interactive 3D Card Hover / Tilt Physics & Dynamic Glare
function initCard3DTilt() {
  const cards = document.querySelectorAll('.glass-panel, .metric-card, .dataset-card');

  cards.forEach(card => {
    let glare = card.querySelector('.card-glare');
    if (!glare) {
      glare = document.createElement('div');
      glare.className = 'card-glare';
      glare.style.cssText = `
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        pointer-events: none;
        border-radius: inherit;
        background: radial-gradient(circle at 50% 50%, rgba(0, 240, 255, 0.14), transparent 65%);
        opacity: 0;
        transition: opacity 0.25s ease;
        z-index: 2;
      `;
      card.style.position = 'relative';
      card.appendChild(glare);
    }

    card.onmouseenter = () => {
      card.style.transition = 'transform 0.08s ease-out, box-shadow 0.2s ease, border-color 0.2s ease';
      glare.style.opacity = '1';
    };

    card.onmousemove = (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const xPercent = (x / rect.width) - 0.5;
      const yPercent = (y / rect.height) - 0.5;

      const rotateX = -yPercent * 12;
      const rotateY = xPercent * 12;

      card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.018, 1.018, 1.018)`;
      glare.style.background = `radial-gradient(circle at ${x}px ${y}px, rgba(0, 240, 255, 0.18), transparent 65%)`;
    };

    card.onmouseleave = () => {
      card.style.transition = 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease, border-color 0.3s ease';
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
      glare.style.opacity = '0';
    };
  });
}
window.initCard3DTilt = initCard3DTilt;

// Live Satellite Orbit Telemetry HUD Ticker
const satelliteFleet = [
  { name: 'ISS (ZARYA)', norad: 25544, alt: 418.4, vel: 27580, inc: 51.64, sensor: 'SAGE III · ECOSTRESS' },
  { name: 'TERRA (EOS AM-1)', norad: 25994, alt: 705.1, vel: 26980, inc: 98.2, sensor: 'MODIS · ASTER · CERES' },
  { name: 'AQUA (EOS PM-1)', norad: 27424, alt: 705.3, vel: 26980, inc: 98.2, sensor: 'AIRS · AMSU-A · CERES' },
  { name: 'SUOMI NPP', norad: 37849, alt: 834.0, vel: 26710, inc: 98.7, sensor: 'VIIRS · CrIS · ATMS' }
];
let activeSatIndex = 0;

function initSatelliteTelemetryTicker() {
  const satNameEl = document.getElementById('telemetry-sat-name');
  const satCoordsEl = document.getElementById('telemetry-sat-coords');
  const satAltEl = document.getElementById('telemetry-sat-alt');
  const satVelEl = document.getElementById('telemetry-sat-vel');
  const satSensorEl = document.getElementById('telemetry-sat-sensor');
  if (!satNameEl) return;

  function updateTelemetry() {
    const sat = satelliteFleet[activeSatIndex];
    const now = Date.now() / 1000;
    const periodSec = (2 * Math.PI * (6371 + sat.alt)) / (sat.vel / 3.6);
    const orbitProgress = (now % periodSec) / periodSec;
    const lat = (Math.sin(orbitProgress * Math.PI * 2) * sat.inc).toFixed(2);
    const lon = (((now / 15) % 360) - 180).toFixed(2);

    satNameEl.textContent = sat.name;
    if (satCoordsEl) satCoordsEl.textContent = `${lat}° N, ${lon}° E`;
    if (satAltEl) satAltEl.textContent = `${sat.alt.toFixed(1)} km`;
    if (satVelEl) satVelEl.textContent = `${(sat.vel / 3600).toFixed(2)} km/s`;
    if (satSensorEl) satSensorEl.textContent = sat.sensor;
  }

  setInterval(updateTelemetry, 1000);
  updateTelemetry();

  window.cycleSatellite = () => {
    activeSatIndex = (activeSatIndex + 1) % satelliteFleet.length;
    updateTelemetry();
    SoundFX.playSwitch();
    showToast(`Switched Orbital Focus: ${satelliteFleet[activeSatIndex].name}`);
  };
}

// Hero 3D Globe HUD Floating Toolbar Actions
let currentGlobeSpeed = 1;
window.toggleGlobeClouds = () => {
  if (!state.heroGlobe) return;
  const isVis = state.heroGlobe.toggleClouds();
  const btn = document.getElementById('btn-toggle-clouds');
  if (btn) btn.classList.toggle('active', isVis);
  SoundFX.playClick();
};

window.toggleGlobeAtmos = () => {
  if (!state.heroGlobe) return;
  const isVis = state.heroGlobe.toggleAtmosphere();
  const btn = document.getElementById('btn-toggle-atmos');
  if (btn) btn.classList.toggle('active', isVis);
  SoundFX.playClick();
};

window.toggleGlobeSats = () => {
  if (!state.heroGlobe) return;
  const isVis = state.heroGlobe.toggleSatellites();
  const btn = document.getElementById('btn-toggle-sats');
  if (btn) btn.classList.toggle('active', isVis);
  SoundFX.playClick();
};

window.cycleGlobeSpeed = () => {
  if (!state.heroGlobe) return;
  const speeds = [1, 2, 4, 0, 0.5];
  const nextIdx = (speeds.indexOf(currentGlobeSpeed) + 1) % speeds.length;
  currentGlobeSpeed = speeds[nextIdx];
  state.heroGlobe.setRotationSpeed(currentGlobeSpeed);
  const btn = document.getElementById('btn-speed-globe');
  if (btn) btn.textContent = `⚡ ${currentGlobeSpeed === 0 ? 'PAUSE' : currentGlobeSpeed + 'x'}`;
  SoundFX.playClick();
};

window.resetGlobeView = () => {
  if (!state.heroGlobe) return;
  state.heroGlobe.resetView();
  SoundFX.playClick();
  showToast('Globe camera view reset');
};

// Global Download triggers
window.downloadCurrentCSV = () => {
  earthScopeApi.downloadCSV(state.activeLocation.lat, state.activeLocation.lon, state.startYear, state.endYear, state.activeLocation.name);
  showToast(`Downloading CSV dossier for ${state.activeLocation.short_name}...`);
};

window.downloadCurrentPDF = () => {
  earthScopeApi.downloadPDF(state.activeLocation.lat, state.activeLocation.lon, state.startYear, state.endYear, state.activeLocation.name);
  showToast(`Generating publication PDF report for ${state.activeLocation.short_name}...`);
};

window.selectLocation = selectLocation;
window.navigateTo = navigateTo;

// Application Bootstrap
document.addEventListener('DOMContentLoaded', async () => {
  initBackgroundCanvas();
  initCard3DTilt();
  initSatelliteTelemetryTicker();

  // 1. Check Backend Connectivity
  try {
    const health = await earthScopeApi.checkHealth();
    state.backendConnected = health.status === 'ok';
    const statusText = document.getElementById('backend-status-text');
    if (statusText) {
      statusText.textContent = health.nasa_power_reachable ? '● Live NASA POWER API Connected' : '● NASA Server Slow / Cache Mode';
    }
  } catch (err) {
    console.warn('Backend offline, running in browser fallback mode.');
    const statusText = document.getElementById('backend-status-text');
    if (statusText) statusText.textContent = '● FastAPI Backend Initializing...';
  }

  // 2. Load Location Presets
  try {
    const locRes = await earthScopeApi.getLocations();
    state.locations = locRes.locations;
    const defaultLoc = state.locations.find(l => l.id === locRes.default_location_id) || state.locations[0];
    if (defaultLoc) state.activeLocation = defaultLoc;

    // Populate dropdowns
    const sel = document.getElementById('global-location-select');
    if (sel) {
      sel.innerHTML = state.locations.map(l => `
        <option value="${l.id}">${l.name}</option>
      `).join('');
      sel.value = state.activeLocation.id;
      sel.addEventListener('change', (e) => selectLocation(e.target.value));
    }
  } catch (err) {
    console.error('Failed to load locations catalog:', err);
  }

  // 3. Initialize Hero Globe
  state.heroGlobe = new EarthScopeGlobe('hero-earth-container', {
    radius: 95,
    autoRotate: true,
    interactive: true,
    onLocationSelect: (loc) => selectLocation(loc.id)
  });
  if (state.locations.length > 0) {
    state.heroGlobe.setLocations(state.locations);
    state.heroGlobe.flyToLocation(state.activeLocation.lat, state.activeLocation.lon);
  }

  // 4. Attach Navigation Buttons
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      navigateTo(btn.dataset.page);
    });
  });

  // 5. Initial Data Load
  await loadActiveLocationData();
});
