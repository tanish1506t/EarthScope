"""
Anomaly Detection and Trend Projections Service
EarthScope Backend
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from scipy import stats

from backend.app.config import PARAMETERS_META
from backend.app.schemas import (
    AnomalyRecord, AnomaliesResponse,
    ProjectionRecord, ProjectionsResponse
)

class AnomalyDetectionService:
    @staticmethod
    def detect_anomalies(df: pd.DataFrame, variable: str = "t2m") -> AnomaliesResponse:
        """
        Calculates calendar-month climatological baseline departures and flags extreme events (|z| > 2.0).
        """
        col = variable.lower()
        meta = PARAMETERS_META.get(variable.upper(), {})
        units = meta.get("units", "°C")

        if df.empty or col not in df.columns:
            return AnomaliesResponse(
                variable=variable,
                units=units,
                baseline_period="N/A",
                total_months=0,
                extreme_count=0,
                threshold_z=2.0,
                all_anomalies=[],
                flagged_anomalies=[],
                monthly_climatology={}
            )

        clean_df = df[["year", "month", col]].dropna()
        if clean_df.empty:
            return AnomaliesResponse(
                variable=variable,
                units=units,
                baseline_period="N/A",
                total_months=0,
                extreme_count=0,
                threshold_z=2.0,
                all_anomalies=[],
                flagged_anomalies=[],
                monthly_climatology={}
            )

        # Baseline: Climatological mean and std for each calendar month (1..12)
        month_groups = clean_df.groupby("month")[col]
        month_means = month_groups.mean().to_dict()
        month_stds = month_groups.std(ddof=1).to_dict()

        # Handle zero or NaN std
        overall_std = float(clean_df[col].std(ddof=1)) or 1.0
        for m in range(1, 13):
            if m not in month_means:
                month_means[m] = float(clean_df[col].mean())
            if m not in month_stds or np.isnan(month_stds[m]) or month_stds[m] < 1e-4:
                month_stds[m] = overall_std

        climatology_dict = {
            f"{m:02d}": {
                "mean": round(float(month_means[m]), 2),
                "std": round(float(month_stds[m]), 2)
            }
            for m in range(1, 13)
        }

        min_year = int(clean_df["year"].min())
        max_year = int(clean_df["year"].max())
        baseline_period = f"{min_year}–{max_year}"

        all_anoms: List[Dict[str, Any]] = []
        flagged: List[AnomalyRecord] = []

        month_names = ["", "January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]

        for idx, row in clean_df.iterrows():
            y = int(row["year"])
            m = int(row["month"])
            val = float(row[col])
            base_m = month_means[m]
            base_s = month_stds[m]

            anom = val - base_m
            z = anom / (base_s if base_s > 1e-4 else 1.0)
            is_extreme = bool(abs(z) > 2.0)
            date_str = f"{y}-{m:02d}"

            # Narrative insight
            m_name = month_names[m]
            direction = "warmer" if anom > 0 else "cooler"
            if "precip" in col or "rain" in col:
                direction = "wetter" if anom > 0 else "drier"

            if is_extreme:
                severity = "Severely" if abs(z) > 3.0 else "Substantially"
                insight = (
                    f"{m_name} {y} was {severity.lower()} {direction} ({anom:+.1f} {units}) "
                    f"than the 12-month baseline mean of {base_m:.1f} {units} (Z = {z:+.2f})."
                )
            else:
                insight = f"Within standard climatological bounds ({anom:+.1f} {units}, Z = {z:+.2f})."

            rec = {
                "date": date_str,
                "year": y,
                "month": m,
                "value": round(val, 2),
                "baseline_mean": round(base_m, 2),
                "baseline_std": round(base_s, 2),
                "anomaly": round(anom, 2),
                "z_score": round(z, 2),
                "is_extreme": is_extreme,
                "insight": insight
            }
            all_anoms.append(rec)

            if is_extreme:
                flagged.append(AnomalyRecord(
                    date=date_str,
                    year=y,
                    month=m,
                    value=round(val, 2),
                    baseline_mean=round(base_m, 2),
                    baseline_std=round(base_s, 2),
                    anomaly=round(anom, 2),
                    z_score=round(z, 2),
                    is_extreme=True,
                    insight=insight
                ))

        # Sort flagged by descending absolute z-score
        flagged.sort(key=lambda r: abs(r.z_score), reverse=True)

        return AnomaliesResponse(
            variable=variable,
            units=units,
            baseline_period=baseline_period,
            total_months=len(all_anoms),
            extreme_count=len(flagged),
            threshold_z=2.0,
            all_anomalies=all_anoms,
            flagged_anomalies=flagged,
            monthly_climatology=climatology_dict
        )

    @staticmethod
    def project_trends(df: pd.DataFrame, variable: str = "t2m", horizon_years: int = 5) -> ProjectionsResponse:
        """
        Calculates straight-line empirical projections with prediction intervals and explicit scientific caveats.
        """
        col = variable.lower()
        meta = PARAMETERS_META.get(variable.upper(), {})
        units = meta.get("units", "°C")
        horizon = max(1, min(10, horizon_years))

        disclaimer = (
            "SCIENTIFIC NOTICE: Straight-line empirical trend extrapolation based strictly on historical OLS regression. "
            "This projection assumes continuation of the empirical rate of change over the selected record. It does NOT "
            "incorporate dynamic Earth-system climate models, aerosol feedbacks, ocean heat content uptake, or greenhouse "
            "gas emission pathways (e.g. CMIP6 SSP scenarios), and should not be construed as an authoritative climate forecast."
        )

        if df.empty or col not in df.columns:
            return ProjectionsResponse(
                variable=variable,
                units=units,
                historical_start_year=2015,
                historical_end_year=2024,
                projected_horizon_years=horizon,
                slope_per_year=None,
                r_squared=None,
                records=[],
                methodology_disclaimer=disclaimer
            )

        # Aggregate annual
        agg_type = meta.get("agg_method", "mean")
        if agg_type == "sum" or col == "prectotcorr":
            counts = df.groupby("year")[col].count()
            good_years = counts[counts >= 10].index
            annual = df[df["year"].isin(good_years)].groupby("year")[col].sum().dropna()
        else:
            annual = df.groupby("year")[col].mean().dropna()

        if len(annual) < 3:
            return ProjectionsResponse(
                variable=variable,
                units=units,
                historical_start_year=int(df["year"].min()),
                historical_end_year=int(df["year"].max()),
                projected_horizon_years=horizon,
                slope_per_year=None,
                r_squared=None,
                records=[],
                methodology_disclaimer=disclaimer
            )

        years = np.array(annual.index, dtype=int)
        y = annual.values.astype(float)
        n = len(years)
        x = np.arange(n, dtype=float)

        slope, intercept, r_val, p_val, std_err = stats.linregress(x, y)
        r_squared = float(r_val ** 2)

        df_deg = max(1, n - 2)
        t_crit = float(stats.t.ppf(0.975, df_deg))
        residuals = y - (intercept + slope * x)
        s_err = np.sqrt(np.sum(residuals ** 2) / df_deg)
        x_mean = np.mean(x)
        ss_x = np.sum((x - x_mean) ** 2) or 1.0

        records: List[ProjectionRecord] = []
        # Historical records
        for i in range(n):
            records.append(ProjectionRecord(
                year=int(years[i]),
                value=round(float(y[i]), 2),
                projected_value=round(float(intercept + slope * i), 2),
                ci_lower=None,
                ci_upper=None,
                type="historical"
            ))

        # Projected horizon
        last_year = int(years[-1])
        for step in range(1, horizon + 1):
            fut_year = last_year + step
            fut_x = float(n - 1 + step)
            fut_y = intercept + slope * fut_x
            # Prediction interval for future observation
            pi_margin = t_crit * s_err * np.sqrt(1.0 + 1.0 / n + (fut_x - x_mean) ** 2 / ss_x)
            records.append(ProjectionRecord(
                year=fut_year,
                value=None,
                projected_value=round(float(fut_y), 2),
                ci_lower=round(float(fut_y - pi_margin), 2),
                ci_upper=round(float(fut_y + pi_margin), 2),
                type="projected"
            ))

        return ProjectionsResponse(
            variable=variable,
            units=units,
            historical_start_year=int(years[0]),
            historical_end_year=last_year,
            projected_horizon_years=horizon,
            slope_per_year=round(float(slope), 4),
            r_squared=round(float(r_squared), 4),
            records=records,
            methodology_disclaimer=disclaimer
        )

anomaly_service = AnomalyDetectionService()
