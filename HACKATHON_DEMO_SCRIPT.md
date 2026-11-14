# 🏆 NASA Space Apps Challenge 2026: Team CodeRex
## Project: EarthScope — Earth System Trend Explorer
### Challenge: "Be An Earth System Trend Detective!"
### Presentation Outline & Live Demonstration Script

---

## ⏱️ Part 1: Hackathon Pitch Outline (3-4 Minutes)

### Slide 1: Title & Hook (30 seconds)
- **Title:** EarthScope — Be An Earth System Trend Detective!
- **Team:** CodeRex
- **The Problem:** Modern climate conversations are often overwhelmed by isolated single-day extreme weather headlines or black-box graphs that lack observational context and rigorous statistical justification. People want to know: *Is this natural variability, or a persistent planetary trend?*
- **The Solution:** EarthScope empowers users to become genuine scientific detectives by pairing live NASA satellite and reanalysis observations with dual-method hypothesis testing, autocorrelation adjustments, and evidence-grounded insights.

### Slide 2: Real NASA Data Ingestion & Quality Control (45 seconds)
- **NASA Source:** NASA Langley Research Center POWER API v2 (modern reanalysis derived from GEOS FP-IT atmospheric models and MERRA-2 assimilation).
- **Core Parameters:** Mean Air Temperature (T2M), Diurnal Max & Min (T2M_MAX, T2M_MIN), Bias-Corrected Precipitation (PRECTOTCORR), Radiative Skin Temperature (TS), Root-Zone Soil Moisture (GWETROOT), and Solar Irradiance (ALLSKY_SFC_SW_DWN).
- **Quality Control Principle:** Zero synthetic data fabrication. NASA fill values (`-999.0`) are strictly preserved as NaNs. Calendar months require $\ge 20$ valid daily records before computing monthly totals.

### Slide 3: The Trend Detective Statistical Engine (60 seconds)
- **Dual-Method Hypothesis Testing:**
  - *Parametric:* Ordinary Least Squares (OLS) with 95% Student's $t$ confidence intervals and $R^2$.
  - *Non-Parametric:* Mann-Kendall monotonic trend test ($Z$-score, $p$-value) and Sen's slope estimator (immune to isolated extreme spikes up to 29% contamination).
- **Physical Persistence:** Lag-1 autocorrelation ($r_1$) analysis and effective sample size ($N_{\text{eff}}$) correction, preventing false-positive statistical claims.
- **Two-Period Comparative Diagnosis:** Welch's unequal-variance $t$-test and Cohen's $d$ effect size comparing baseline decades to modern windows.

### Slide 4: Ultra-Dynamic Space-Age UI & Key Insights (45 seconds)
- **Aesthetic:** Deep midnight-navy, cyan/electric-blue glow, glassmorphism stat cards, and an interactive 3D WebGL rotating Earth with live target coordinate pinning.
- **Evidence-Grounded AI Insights:** Automated scientific synthesis that quotes exact calculated numbers, observations, and $p$-values with strict attribution boundaries.
- **Export & Reproducibility:** Instant export of CSV datasets, high-res charts, and formal printable scientific dossiers.

---

## 🎬 Part 2: Step-by-Step Live Demonstration Script

### Act 1: The Launch & 3D Earth Orbit (0:00 - 0:45)
1. **Show Screen:** Open `http://localhost:8501`.
2. **Presenter Script:**
   > *"Judges, welcome to EarthScope — built for the NASA Space Apps Challenge 2026 by Team CodeRex! Notice our futuristic command center. In the hero section, an interactive 3D WebGL Earth rotates in real time with our active sensor pin placed directly over our featured location: Nashik, Maharashtra, India — a crucial agricultural hub experiencing intense monsoon transitions."*
3. **Action:** Rotate the 3D globe with the mouse, pointing out the pulsing cyan target marker.
4. **Presenter Script:**
   > *"EarthScope is not a static mockup. It connects directly to NASA's POWER API v2. Look at our metrics: 3,653 usable daily records loaded over 10 years, with 0% data loss, and immediate Mann-Kendall hypothesis testing."*

### Act 2: Temperature & Diurnal Thermal Envelope (0:45 - 1:30)
1. **Action:** Click on **"🌡️ Temperature Explorer"** in the sidebar.
2. **Presenter Script:**
   > *"Let's step into the shoes of an Earth System Trend Detective. Here is the Diurnal Thermal Envelope: daytime peak solar heating in red, nighttime radiative cooling in blue, and the 24-hour mean in cyan. Right below it, EarthScope computes the Diurnal Temperature Range (DTR). Notice how night minimums and daytime maximums are shifting, a key fingerprint of atmospheric radiative trapping. We can toggle between Celsius, Fahrenheit, and Kelvin in real time, and explore the 12-month annual climatological cycle with $\pm 1\sigma$ standard deviation bands."*

### Act 3: Precipitation Dynamics & Drought Streaks (1:30 - 2:15)
1. **Action:** Click on **"🌧️ Precipitation Explorer"** in the sidebar.
2. **Presenter Script:**
   > *"Next, we inspect hydrological dynamics. EarthScope breaks down NASA's bias-corrected PRECTOTCORR records into daily events and cumulative annual mass curves. Notice our intensity pie chart: 81% of days are dry, but episodic convective pulses deliver over 25 mm in a single day. EarthScope automatically calculates the longest continuous dry streak — in Nashik's case, 142 consecutive dry days between post-monsoon and pre-monsoon, providing critical intelligence for reservoir managers."*

### Act 4: The Trend Analysis Lab & Statistical Rigor (2:15 - 3:00)
1. **Action:** Click on **"🔬 Trend Analysis Lab"** in the sidebar.
2. **Presenter Script:**
   > *"Here is the core detective lab. Rather than relying on simple linear regression alone, EarthScope pairs parametric OLS with the non-parametric Mann-Kendall test and Sen's slope median estimator. Look at our two-period comparison workbench: we can compare the 2015–2019 baseline against 2020–2024. A Welch's $t$-test determines whether the observed shift is statistically significant ($p < 0.05$) or within natural climate noise. Crucially, our serial autocorrelation engine computes lag-1 correlation and adjusts the effective sample size ($N_{\text{eff}}$) so we never overstate certainty."*

### Act 5: Evidence-Grounded AI Insights & Dossier Export (3:00 - 3:45)
1. **Action:** Click on **"🤖 AI Scientific Insights"** in the sidebar, then scroll down to the report download drawer.
2. **Presenter Script:**
   > *"Finally, how do we communicate complex findings to students and policymakers? Our AI Scientific Assistant generates clear, evidence-grounded summaries: 'Across the selected period, mean temperature changed by +X °C based on Y usable NASA observations...' It never hallucinates numbers and clearly outlines attribution boundaries. With a single click, users can download the entire verified dataset as a CSV, or export a formal print-ready Scientific Investigation Dossier in Markdown or HTML. That is EarthScope: authentic NASA science, uncompromising statistical rigor, and an intuitive space-age interface. Thank you!"*
