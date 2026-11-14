"""
Data Sources and Scientific Methodology Page for EarthScope
Thoroughly documents data provenance, parameters, mathematical formulas, and scientific limitations.
"""

import streamlit as st
import pandas as pd

from earthscope.config import PARAMETERS_META


def render_methodology_page() -> None:
    """
    Renders the Data Sources and Methodology page.
    """
    st.markdown("### 📚 Scientific Methodology & Data Sources Documentation")

    st.html("""
    <div style="font-size: 13px; color: #94a3b8; margin-bottom: 20px;">
        Comprehensive documentation of satellite data ingestion, quality-control filtering,
        mathematical equations for statistical tests, and physical attribution boundaries.
    </div>
    """)

    # Tabs for structured reading
    tab_data, tab_math, tab_limits, tab_refs = st.tabs([
        "🛰️ NASA Datasets & Variables",
        "📐 Mathematical Framework",
        "⚠️ Attribution & Limitations",
        "🔗 Official NASA Citations"
    ])

    with tab_data:
        st.markdown("#### Operational NASA Earth Observation Parameters")
        st.markdown("""
        EarthScope ingests daily meteorological and land-surface data from the **NASA Langley Research Center POWER Project (v2.0)**.
        All data originates from NASA's modern reanalysis: **MERRA-2** (Modern-Era Retrospective Analysis for Research and Applications, Version 2)
        and the **GEOS FP-IT** (Goddard Earth Observing System Forward Processing for Instrument Teams) atmospheric model.
        """)

        param_rows = []
        for p, meta in PARAMETERS_META.items():
            param_rows.append({
                "Parameter Code": p,
                "Scientific Name": meta.get("name", p),
                "Physical Units": meta.get("units", ""),
                "Valid Range": f"[{meta.get('min_valid')}, {meta.get('max_valid')}]",
                "Aggregation Method": meta.get("agg_method", "mean").capitalize(),
                "Description": meta.get("description", "")
            })

        st.dataframe(pd.DataFrame(param_rows), hide_index=True)

        st.markdown("##### Missing Value Quarantining Protocol")
        st.markdown(r"""
        - **Fill Value Identifier:** NASA POWER encodes missing, unavailable, or corrupted observations with the fill flag **`-999.0`**.
        - **Quarantine Rule:** All `-999.0` or values $\le -900.0$ are immediately coerced to IEEE `NaN`.
        - **No Synthetic Fabrication:** EarthScope **strictly forbids** filling gaps with synthetic or interpolated points for trend calculation.
        - **Monthly Thresholding:** A calendar month requires at least **20 valid daily observations** to compute an aggregate. If valid days $< 20$, the monthly aggregate is classified as `NaN` to prevent biased seasonal distortions.
        """)

    with tab_math:
        st.markdown("#### Mathematical & Statistical Framework")

        st.markdown(r"""
        ##### 1. Ordinary Least Squares (OLS) Linear Regression
        Fits the parametric model $y(t) = m \cdot t + c$, minimizing sum of squared residuals:
        $$m = \frac{\sum_{i=1}^n (t_i - \bar{t})(y_i - \bar{y})}{\sum_{i=1}^n (t_i - \bar{t})^2}$$
        
        The standard error of the slope ($SE_m$) and $(1 - \alpha)$ confidence interval:
        $$SE_m = \sqrt{\frac{\sum (y_i - \hat{y}_i)^2}{(n - 2) \sum (t_i - \bar{t})^2}}$$
        $$\text{CI}_{95\%} = m \pm t_{\alpha/2, \, n-2} \cdot SE_m$$

        ##### 2. Non-Parametric Mann-Kendall Trend Test
        Evaluates monotonic trends without assuming normal residual distributions:
        $$S = \sum_{k=1}^{n-1} \sum_{j=k+1}^n \text{sgn}(x_j - x_k)$$
        $$\text{Var}(S) = \frac{n(n-1)(2n+5) - \sum_{i=1}^g t_i(t_i - 1)(2t_i + 5)}{18}$$
        $$Z = \begin{cases} \frac{S - 1}{\sqrt{\text{Var}(S)}} & \text{if } S > 0 \\ 0 & \text{if } S = 0 \\ \frac{S + 1}{\sqrt{\text{Var}(S)}} & \text{if } S < 0 \end{cases}$$
        Two-tailed significance evaluates $p = 2(1 - \Phi(|Z|))$.

        ##### 3. Theil-Sen Robust Slope Estimator
        Median of all pairwise slopes across observation pairs $(x_j, x_k)$ where $j > k$:
        $$Q = \text{median}\left( \frac{x_j - x_k}{j - k} \right)$$
        Has a high breakdown point (~29%), protecting trend rates from episodic volcanic or sensor spike outliers.

        ##### 4. Autocorrelation & Effective Sample Size ($N_{\text{eff}}$)
        For time series with lag-1 serial autocorrelation $r_1$, effective degrees of freedom are adjusted:
        $$N_{\text{eff}} = N \cdot \frac{1 - r_1}{1 + r_1}$$
        """)

    with tab_limits:
        st.markdown("#### Attribution Boundaries & Physical Limitations")
        st.html("""
        <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; border-radius: 10px; padding: 18px; font-size: 13px; color: #cbd5e1; line-height: 1.6;">
            <div style="font-weight: 700; color: #f59e0b; margin-bottom: 8px;">CRITICAL SCIENTIFIC ATTRIBUTION PRINCIPLES</div>
            <ol style="margin: 0; padding-left: 20px;">
                <li style="margin-bottom: 8px;">
                    <strong>Correlation is Not Causation:</strong> An empirical positive slope in temperature ($p < 0.05$) demonstrates that warming has occurred historically. It does not by itself isolate the proportion driven by greenhouse gas emissions vs regional land-use change, urban heat islands, or deforestation.
                </li>
                <li style="margin-bottom: 8px;">
                    <strong>Spatial Averaging vs Microclimates:</strong> NASA POWER values reflect grid cells (~50 km across). Local valleys, urban canyons, and microclimates may deviate from the grid-cell spatial mean.
                </li>
                <li style="margin-bottom: 8px;">
                    <strong>Multi-Decadal Climate Oscillations:</strong> Trends spanning 10–20 years can be modulated by natural ocean-atmosphere modes like ENSO (El Niño-Southern Oscillation), PDO (Pacific Decadal Oscillation), and IOD (Indian Ocean Dipole). Short-term trends should not be extrapolated into long-term climate projections without Earth System model simulations.
                </li>
            </ol>
        </div>
        """)

    with tab_refs:
        st.markdown("#### Official NASA Documentation & References")
        st.markdown("""
        - **NASA POWER Project Portal:**  
          [https://power.larc.nasa.gov/](https://power.larc.nasa.gov/)
        - **NASA POWER API Documentation:**  
          [https://power.larc.nasa.gov/docs/services/api/temporal/daily/point/](https://power.larc.nasa.gov/docs/services/api/temporal/daily/point/)
        - **NASA Earthdata Platform:**  
          [https://www.earthdata.nasa.gov/](https://www.earthdata.nasa.gov/)
        - **MERRA-2 Overview (GMAO / NASA GSFC):**  
          Gelaro, R., et al. (2017). *The Modern-Era Retrospective Analysis for Research and Applications, Version 2 (MERRA-2)*. Journal of Climate, 30(14), 5419-5454.
        - **Mann-Kendall Test Formulation:**  
          Kendall, M.G. (1975). *Rank Correlation Methods*. Charles Griffin, London.
        - **Sen's Slope Formulation:**  
          Sen, P.K. (1968). *Estimates of the Regression Coefficient Based on Kendall's Tau*. J. American Statistical Association.
        """)
