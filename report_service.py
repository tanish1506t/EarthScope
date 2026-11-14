"""
Report Generation Service
Generates professional CSV and PDF reports using ReportLab with publication-grade layout.
"""

import io
from datetime import datetime, timezone
from typing import Dict, Any, List
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)

from backend.app.schemas import ClimateRecord, ClimateSummary, TrendResult, AnomaliesResponse

class ReportService:
    @staticmethod
    def generate_csv(
        records: List[ClimateRecord],
        location_name: str,
        lat: float,
        lon: float,
        retrieval_time: str
    ) -> str:
        """
        Creates well-structured, standard CSV with scientific header metadata.
        """
        output = io.StringIO()
        output.write("# EARTHSCOPE CLIMATE DATA DOSSIER\n")
        output.write(f"# Location: {location_name}\n")
        output.write(f"# Coordinates: Latitude {lat:.4f}, Longitude {lon:.4f}\n")
        output.write(f"# Retrieved At: {retrieval_time}\n")
        output.write("# Primary Source: NASA Langley Research Center POWER Project v2 (MERRA-2 / GEOS FP-IT)\n")
        output.write("# Parameter Units: T2M, T2M_MAX, T2M_MIN, TS in °C; PRECTOTCORR in mm; RH2M in %; WS2M in m/s\n")
        output.write("# Missing Values: Encoded as blank (never fabricated or zeroed)\n")
        output.write("# ----------------------------------------------------------------------------------------\n")
        
        df_rows = []
        for r in records:
            df_rows.append({
                "month": r.date,
                "location": location_name,
                "latitude": lat,
                "longitude": lon,
                "temperature_2m_c": r.t2m if r.t2m is not None else "",
                "temp_max_2m_c": r.t2m_max if r.t2m_max is not None else "",
                "temp_min_2m_c": r.t2m_min if r.t2m_min is not None else "",
                "precipitation_mm": r.prectotcorr if r.prectotcorr is not None else "",
                "relative_humidity_pct": r.rh2m if r.rh2m is not None else "",
                "skin_temperature_c": r.ts if r.ts is not None else "",
                "wind_speed_2m_ms": r.ws2m if r.ws2m is not None else "",
                "data_source": r.source
            })

        df = pd.DataFrame(df_rows)
        df.to_csv(output, index=False)
        return output.getvalue()

    @staticmethod
    def generate_pdf(
        location_name: str,
        lat: float,
        lon: float,
        summary: ClimateSummary,
        trend: TrendResult,
        anomalies: AnomaliesResponse,
        records: List[ClimateRecord]
    ) -> bytes:
        """
        Builds a multi-page PDF document using ReportLab.
        """
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch
        )

        styles = getSampleStyleSheet()
        
        # Custom palette: Space dark navy & cyan accents
        c_primary = colors.HexColor("#061b36")
        c_accent = colors.HexColor("#00bcd4")
        c_dark = colors.HexColor("#1e293b")
        c_light = colors.HexColor("#f8fafc")
        c_border = colors.HexColor("#cbd5e1")

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=c_primary
        )

        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569")
        )

        h2_style = ParagraphStyle(
            "Heading2Custom",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=c_primary,
            spaceBefore=12,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            "BodyCustom",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=c_dark
        )

        callout_style = ParagraphStyle(
            "CalloutCustom",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#334155")
        )

        story = []

        # Header banner
        story.append(Paragraph("EARTHSCOPE — SCIENTIFIC CLIMATE INVESTIGATION REPORT", title_style))
        story.append(Paragraph(
            f"NASA Space Apps Challenge 2026 | Challenge: 'Be An Earth System Trend Detective!'<br/>"
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC | Data Source: NASA POWER API v2",
            subtitle_style
        ))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=2, spaceAfter=10))

        # Metadata & Location Overview Table
        date_start = records[0].date if records else "N/A"
        date_end = records[-1].date if records else "N/A"

        meta_data = [
            [Paragraph("<b>Target Location:</b>", body_style), Paragraph(location_name, body_style),
             Paragraph("<b>Observation Range:</b>", body_style), Paragraph(f"{date_start} to {date_end}", body_style)],
            [Paragraph("<b>Coordinates:</b>", body_style), Paragraph(f"{lat:.4f}° N/S, {lon:.4f}° E/W", body_style),
             Paragraph("<b>Records Analyzed:</b>", body_style), Paragraph(f"{summary.valid_records} valid / {summary.total_records} total", body_style)],
            [Paragraph("<b>Completeness:</b>", body_style), Paragraph(f"{summary.completeness_pct}% (Strict QA)", body_style),
             Paragraph("<b>Upstream Model:</b>", body_style), Paragraph("NASA GEOS FP-IT / MERRA-2", body_style)]
        ]

        t_meta = Table(meta_data, colWidths=[1.5*inch, 2.2*inch, 1.5*inch, 2.3*inch])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), c_light),
            ('BOX', (0, 0), (-1, -1), 0.5, c_border),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_meta)
        story.append(Spacer(1, 10))

        # Core Climate Indicators
        story.append(Paragraph("1. Core Climatological Metrics", h2_style))
        
        metrics_data = [
            ["Metric Parameter", "Value", "Units", "Scientific Interpretation"],
            ["Average 2m Temperature", f"{summary.mean_temperature if summary.mean_temperature is not None else '—'}", "°C", "Long-term temporal baseline mean"],
            ["Maximum Recorded Temp", f"{summary.max_temperature if summary.max_temperature is not None else '—'}", "°C", "Peak monthly thermal excursion"],
            ["Minimum Recorded Temp", f"{summary.min_temperature if summary.min_temperature is not None else '—'}", "°C", "Lowest recorded monthly baseline"],
            ["Mean Annual Precipitation", f"{summary.annual_precipitation if summary.annual_precipitation is not None else '—'}", "mm / yr", "Accumulated hydrological flux"],
            ["Warmest Year on Record", f"{summary.warmest_year or '—'}", "Year", f"Mean: {summary.warmest_year_mean or '—'} °C"]
        ]

        t_metrics = Table(metrics_data, colWidths=[2.0*inch, 1.2*inch, 1.0*inch, 3.3*inch])
        t_metrics.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), c_primary),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, c_border),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light])
        ]))
        story.append(t_metrics)
        story.append(Spacer(1, 10))

        # Trend and Statistical Hypothesis Testing
        story.append(Paragraph("2. Trend Analysis and Statistical Significance", h2_style))
        
        slope_dec_str = f"{trend.slope_per_decade:+.3f}" if trend.slope_per_decade is not None else "—"
        slope_yr_str = f"{trend.slope_per_year:+.4f}" if trend.slope_per_year is not None else "—"
        r2_str = f"{trend.r_squared:.3f}" if trend.r_squared is not None else "—"
        p_str = f"{trend.p_value:.4f}" if trend.p_value is not None else "—"
        ci_str = f"[{trend.ci_95_lower:+.4f}, {trend.ci_95_upper:+.4f}]" if (trend.ci_95_lower is not None and trend.ci_95_upper is not None) else "N/A"
        mk_z_str = f"{trend.mann_kendall_z:.2f}" if trend.mann_kendall_z is not None else "—"
        sens_str = f"{trend.sens_slope:+.4f}" if trend.sens_slope is not None else "—"

        trend_summary_text = (
            f"<b>OLS Linear Regression:</b> Rate of change is <b>{slope_dec_str} °C / decade</b> "
            f"(slope: {slope_yr_str} °C/yr, R² = {r2_str}, p = {p_str}). "
            f"The 95% Student's t confidence interval on slope is {ci_str}.<br/>"
            f"<b>Non-Parametric Mann-Kendall Test:</b> Z = {mk_z_str}, "
            f"Sen's Slope Median Estimator = {sens_str} °C/yr. "
            f"<b>Verdict:</b> {trend.verdict}"
        )
        story.append(Paragraph(trend_summary_text, body_style))
        story.append(Spacer(1, 8))

        # Top Extreme Anomalies Table
        story.append(Paragraph("3. Flagged Climatological Anomalies (|Z| > 2.0)", h2_style))
        if anomalies.flagged_anomalies:
            anom_data = [["Month", "Observed", "Baseline Mean", "Anomaly", "Z-Score", "Scientific Assessment"]]
            for a in anomalies.flagged_anomalies[:6]:  # Top 6
                anom_data.append([
                    a.date,
                    f"{a.value:.1f} °C",
                    f"{a.baseline_mean:.1f} °C",
                    f"{a.anomaly:+.2f} °C",
                    f"{a.z_score:+.2f}",
                    a.insight[:48] + "..." if len(a.insight) > 48 else a.insight
                ])
            t_anom = Table(anom_data, colWidths=[1.0*inch, 1.0*inch, 1.1*inch, 1.0*inch, 0.9*inch, 2.5*inch])
            t_anom.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('GRID', (0, 0), (-1, -1), 0.5, c_border),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light])
            ]))
            story.append(t_anom)
        else:
            story.append(Paragraph("<i>No monthly anomalies exceeded the strict |Z| > 2.0 standard deviation threshold over this period.</i>", body_style))

        story.append(Spacer(1, 12))

        # Methodology and Attribution Boundaries
        story.append(Paragraph("4. Scientific Methodology & Attribution Boundaries", h2_style))
        method_notes = (
            "• <b>Missing Values Protocol:</b> In accordance with NASA guidelines, missing points (-999.0) are quarantined as NaN "
            "and excluded from statistical sums or distributions. Values are never fabricated or zeroed.<br/>"
            "• <b>Precipitation Aggregation:</b> NASA POWER monthly precipitation rates (mm/day) are multiplied by the exact days in each calendar month to yield true monthly millimeter totals.<br/>"
            "• <b>Attribution Notice:</b> Empirical statistical trends quantify historical observational trajectory but do not prove anthropogenic causation alone without regional attribution modeling. Linear projections are empirical references, not future climate scenario forecasts."
        )
        story.append(Paragraph(method_notes, callout_style))

        doc.build(story)
        buf.seek(0)
        return buf.getvalue()

report_service = ReportService()
