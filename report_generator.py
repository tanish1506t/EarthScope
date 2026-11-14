"""
Scientific Report Generator Module
Compiles complete investigation findings, statistical tables, and citations into
exportable Markdown and print-ready HTML reports.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

from earthscope.config import APP_NAME, TEAM_NAME, CHALLENGE_TITLE, PARAMETERS_META


def generate_markdown_report(
    location_name: str,
    lat: float,
    lon: float,
    start_year: int,
    end_year: int,
    stats_dict: Dict[str, Dict[str, Any]],
    trend_dict: Dict[str, Dict[str, Any]],
    mk_dict: Dict[str, Dict[str, Any]],
    uncertainty_dict: Dict[str, Dict[str, Any]],
    retrieval_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generates a formal Markdown investigation report.
    """
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    retrieved_time = retrieval_metadata.get("retrieved_at", now_str) if retrieval_metadata else now_str

    md = f"""# {APP_NAME} — Earth System Investigation Report
**NASA Space Apps Challenge 2026** | **Challenge:** *{CHALLENGE_TITLE}*  
**Team:** {TEAM_NAME}  
**Report Generated:** {now_str}  
**Target Location:** {location_name} (Latitude: {lat:.4f}°, Longitude: {lon:.4f}°)  
**Investigation Temporal Window:** {start_year}–{end_year}  
**Primary Observation Platform:** NASA POWER Modern-Era Retrospective Analysis / GEOS FP-IT Assimilation  

---

## 1. Executive Summary & Objective

This report investigates temporal environmental shifts and climate trends for **{location_name}** using authentic NASA Earth observations. The investigation follows rigorous statistical protocols: parametric Ordinary Least Squares (OLS) regression with 95% confidence intervals, non-parametric Mann-Kendall trend tests, Sen's slope estimations, and observational completeness quality control.

---

## 2. Statistical Findings by Environmental Variable

| Variable | Usable Obs | Missing % | Baseline Mean | Decadal Rate | OLS p-value | Mann-Kendall Z | Statistical Significance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""

    for var, s_info in stats_dict.items():
        meta = PARAMETERS_META.get(var, {})
        u = meta.get("units", "")
        v_name = meta.get("name", var)
        n_obs = s_info.get("valid_observations", 0)
        m_pct = s_info.get("missing_pct", 0.0)
        mean_v = s_info.get("mean", "N/A")

        t_info = trend_dict.get(var, {})
        dec_rate = t_info.get("slope_per_decade", "N/A")
        p_val = t_info.get("p_value", 1.0)
        is_sig = t_info.get("is_significant", False)

        m_info = mk_dict.get(var, {})
        mk_z = m_info.get("z_statistic", "N/A")

        sig_badge = "Significant (p < 0.05)" if is_sig else "Not Significant (p ≥ 0.05)"
        dec_str = f"{dec_rate:+.3f} {u}" if isinstance(dec_rate, (int, float)) else str(dec_rate)
        p_str = f"{p_val:.4f}" if isinstance(p_val, (int, float)) else str(p_val)
        z_str = f"{mk_z:.2f}" if isinstance(mk_z, (int, float)) else str(mk_z)

        md += f"| **{v_name}** | {n_obs:,} | {m_pct}% | {mean_v} {u} | {dec_str}/dec | {p_str} | {z_str} | {sig_badge} |\n"

    md += f"""
---

## 3. Observational Uncertainty & Completeness Assessment

"""
    for var, u_info in uncertainty_dict.items():
        v_name = PARAMETERS_META.get(var, {}).get("name", var)
        md += f"""### {v_name}
- **Observational Completeness Rating:** {u_info.get('completeness_rating', 'N/A')}
- **Max Consecutive Missing Gap:** {u_info.get('max_consecutive_gap_days', 0)} calendar days
- **Lag-1 Autocorrelation ($r_1$):** {u_info.get('lag1_autocorrelation', 'N/A')}
- **Effective Sample Size ($N_{{\\text{{eff}}}}$):** {u_info.get('effective_sample_size', 'N/A')}
- **Statistical Persistence Note:** {u_info.get('autocorr_assessment', 'N/A')}

"""

    md += f"""---

## 4. Methodology & Mathematical Framework

1. **Ordinary Least Squares (OLS) Linear Regression:**
   $$y = m \\cdot t + c$$
   Slope confidence intervals are derived via Student's t-distribution with $df = n - 2$ at $\\alpha = 0.05$:
   $$m \\pm t_{{1-\\alpha/2, df}} \\cdot \\text{{SE}}(m)$$

2. **Non-Parametric Mann-Kendall Trend Test:**
   $$S = \\sum_{{k=1}}^{{n-1}} \\sum_{{j=k+1}}^n \\text{{sgn}}(x_j - x_k)$$
   $$\\text{{Var}}(S) = \\frac{{n(n-1)(2n+5) - \\sum t_i(t_i-1)(2t_i+5)}}{{18}}$$
   Standardized Z-scores evaluate monotonicity without assuming normal error distributions.

3. **Sen's Slope Estimator:**
   $$Q_{{\\text{{med}}}} = \\text{{median}}\\left(\\frac{{x_j - x_k}}{{j - k}}\\right) \\quad \\forall \\, j > k$$

4. **Missing Data Handling:**
   NASA POWER fill values (`-999.0`) are quarantined as `NaN`. Precipitation summaries are normalized only when monthly valid days satisfy threshold limits ($n_{{\\text{{valid}}}} \\ge 20$).

---

## 5. Scientific Limitations & Attribution Boundaries

> **Important Boundary Statement:** The trends documented in this report represent empirical measurements from satellite retrievals and meteorological assimilation models. Statistical trend significance ($p < 0.05$) does not, in isolation, prove direct anthropogenic causality or decouple regional climate anomalies from multidecadal oceanic oscillations (e.g., ENSO, IOD, AMO).

---

## 6. Data Provenance & Acknowledgments

- **Primary Source:** NASA Langley Research Center (LaRC) POWER Project
- **API Endpoint:** `https://power.larc.nasa.gov/api/temporal/daily/point`
- **Data Retrieved At:** {retrieved_time}
- **Produced By:** Team CodeRex for the NASA Space Apps Challenge 2026.
"""
    return md


def generate_html_report(md_content: str, location_name: str) -> str:
    """
    Wraps markdown content into a standalone, styled HTML document ready for printing or viewing.
    """
    import html
    # Simple conversion of markdown headers and tables into clean HTML
    lines = md_content.split("\n")
    html_body = []
    in_table = False

    for line in lines:
        if line.startswith("# "):
            html_body.append(f"<h1 style='color: #00f0ff; border-bottom: 2px solid #334155; padding-bottom: 8px;'>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            html_body.append(f"<h2 style='color: #38bdf8; margin-top: 24px;'>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            html_body.append(f"<h3 style='color: #e2e8f0; margin-top: 16px;'>{html.escape(line[4:])}</h3>")
        elif line.startswith("> "):
            html_body.append(f"<blockquote style='border-left: 3px solid #f59e0b; background: rgba(245,158,11,0.1); padding: 10px 16px; margin: 12px 0; color: #fde68a;'>{html.escape(line[2:])}</blockquote>")
        elif line.startswith("- "):
            html_body.append(f"<li style='margin-bottom: 4px; color: #cbd5e1;'>{html.escape(line[2:])}</li>")
        elif line.startswith("| ") and "---" not in line:
            cells = [c.strip() for c in line.strip().split("|")[1:-1]]
            tag = "th style='background: #1e293b; color: #38bdf8; padding: 8px 12px; border: 1px solid #334155; text-align: left;'" if not in_table else "td style='padding: 8px 12px; border: 1px solid #334155; color: #e2e8f0;'"
            row_html = "".join([f"<{tag}>{html.escape(c)}</{tag.split()[0]}>" for c in cells])
            if not in_table:
                html_body.append("<table style='width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px;'>")
                html_body.append(f"<tr>{row_html}</tr>")
                in_table = True
            else:
                html_body.append(f"<tr>{row_html}</tr>")
        elif in_table and not line.startswith("|"):
            html_body.append("</table>")
            in_table = False
            if line.strip():
                html_body.append(f"<p style='color: #cbd5e1; line-height: 1.6;'>{html.escape(line)}</p>")
        elif line.startswith("---"):
            html_body.append("<hr style='border: 0; border-top: 1px solid #334155; margin: 24px 0;'>")
        elif line.strip():
            html_body.append(f"<p style='color: #cbd5e1; line-height: 1.6;'>{html.escape(line)}</p>")

    if in_table:
        html_body.append("</table>")

    doc = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>EarthScope Report - {html.escape(location_name)}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #081226;
            color: #f8fafc;
            padding: 40px;
            max-width: 900px;
            margin: 0 auto;
        }}
        @media print {{
            body {{
                background: #ffffff;
                color: #000000;
                padding: 20px;
            }}
            h1, h2, h3 {{ color: #000000 !important; }}
            table, td, th {{ border-color: #cccccc !important; color: #000000 !important; }}
            th {{ background: #f0f0f0 !important; }}
            p, li {{ color: #333333 !important; }}
            blockquote {{ background: #fafafa !important; border-left-color: #ff9900 !important; color: #333333 !important; }}
        }}
    </style>
</head>
<body>
    {''.join(html_body)}
</body>
</html>"""
    return doc
