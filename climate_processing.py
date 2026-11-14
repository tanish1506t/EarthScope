"""
Climate Data Processing Service
Cleans, validates, and transforms NASA POWER payloads into scientific data structures.
"""

import calendar
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from backend.app.config import PARAMETERS_META, settings
from backend.app.schemas import ClimateRecord, ClimateSummary

def is_valid_val(v: Any) -> bool:
    if v is None:
        return False
    try:
        f = float(v)
        return f > -900.0 and not np.isnan(f)
    except (ValueError, TypeError):
        return False

def clean_value(v: Any) -> Optional[float]:
    if is_valid_val(v):
        return round(float(v), 3)
    return None

class ClimateProcessingService:
    @staticmethod
    def process_monthly_payload(payload: Dict[str, Any], location_name: str) -> Tuple[List[ClimateRecord], ClimateSummary, pd.DataFrame]:
        """
        Parses raw NASA POWER monthly API payload into structured ClimateRecord objects,
        summary statistics, and a cleaned pandas DataFrame for statistical modeling.
        """
        if "properties" not in payload or "parameter" not in payload["properties"]:
            raise ValueError("Malformed NASA POWER payload: missing 'properties.parameter'")

        params = payload["properties"]["parameter"]
        meta = payload.get("_retrieval_metadata", {})
        
        # Primary parameters
        t2m_dict = params.get("T2M", {})
        t2m_max_dict = params.get("T2M_MAX", {})
        t2m_min_dict = params.get("T2M_MIN", {})
        precip_dict = params.get("PRECTOTCORR", {})
        rh_dict = params.get("RH2M", {})
        ts_dict = params.get("TS", {})
        ws_dict = params.get("WS2M", {})

        # Collect and sort all valid monthly keys (filter out '13' which is annual in NASA POWER)
        all_keys = set()
        for p_dict in [t2m_dict, precip_dict, t2m_max_dict, t2m_min_dict, rh_dict, ts_dict, ws_dict]:
            for k in p_dict.keys():
                if len(k) == 6 and k.isdigit() and k[4:6] != "13":
                    all_keys.add(k)

        sorted_keys = sorted(list(all_keys))
        records: List[ClimateRecord] = []
        df_rows = []

        for k in sorted_keys:
            year = int(k[:4])
            month = int(k[4:6])
            if month < 1 or month > 12:
                continue

            date_str = f"{year}-{month:02d}"
            days_in_month = calendar.monthrange(year, month)[1]

            t2m_val = clean_value(t2m_dict.get(k))
            t2m_max_val = clean_value(t2m_max_dict.get(k))
            t2m_min_val = clean_value(t2m_min_dict.get(k))
            
            # NASA POWER monthly PRECTOTCORR is mm/day rate.
            # Total monthly rainfall in mm = rate * days_in_month
            precip_rate = clean_value(precip_dict.get(k))
            if precip_rate is not None:
                precip_total = round(precip_rate * days_in_month, 2)
            else:
                precip_total = None

            rh_val = clean_value(rh_dict.get(k))
            ts_val = clean_value(ts_dict.get(k))
            ws_val = clean_value(ws_dict.get(k))

            rec = ClimateRecord(
                date=date_str,
                year=year,
                month=month,
                t2m=t2m_val,
                t2m_max=t2m_max_val,
                t2m_min=t2m_min_val,
                prectotcorr=precip_total,
                rh2m=rh_val,
                ts=ts_val,
                ws2m=ws_val,
                source="NASA POWER"
            )
            records.append(rec)

            df_rows.append({
                "date": date_str,
                "year": year,
                "month": month,
                "t2m": t2m_val,
                "t2m_max": t2m_max_val,
                "t2m_min": t2m_min_val,
                "prectotcorr": precip_total,
                "rh2m": rh_val,
                "ts": ts_val,
                "ws2m": ws_val
            })

        df = pd.DataFrame(df_rows)
        if not df.empty:
            df["datetime"] = pd.to_datetime(df["date"] + "-01")
            df = df.set_index("datetime")

        # Compute summary metrics
        summary = ClimateProcessingService._compute_summary(df, records)
        return records, summary, df

    @staticmethod
    def _compute_summary(df: pd.DataFrame, records: List[ClimateRecord]) -> ClimateSummary:
        if df.empty:
            return ClimateSummary()

        total_rec = len(records)
        t_series = df["t2m"].dropna()
        valid_rec = len(t_series)
        completeness = round((valid_rec / total_rec * 100.0), 1) if total_rec > 0 else 0.0

        mean_temp = round(float(t_series.mean()), 2) if not t_series.empty else None
        max_temp = round(float(t_series.max()), 2) if not t_series.empty else None
        min_temp = round(float(t_series.min()), 2) if not t_series.empty else None

        # Annual aggregates
        # Group by year for temperature and precipitation
        yearly_t = df.groupby("year")["t2m"].mean().dropna()
        warmest_year = int(yearly_t.idxmax()) if not yearly_t.empty else None
        coldest_year = int(yearly_t.idxmin()) if not yearly_t.empty else None
        warmest_year_mean = round(float(yearly_t.max()), 2) if not yearly_t.empty else None

        # Annual precipitation: only consider years with at least 10 valid months
        precip_valid_counts = df.groupby("year")["prectotcorr"].count()
        complete_years = precip_valid_counts[precip_valid_counts >= 10].index

        if len(complete_years) > 0:
            yearly_precip = df[df["year"].isin(complete_years)].groupby("year")["prectotcorr"].sum()
            avg_annual_rainfall = round(float(yearly_precip.mean()), 1)
            wettest_year = int(yearly_precip.idxmax()) if not yearly_precip.empty else None
        else:
            avg_annual_rainfall = None
            wettest_year = None

        return ClimateSummary(
            mean_temperature=mean_temp,
            max_temperature=max_temp,
            min_temperature=min_temp,
            annual_precipitation=avg_annual_rainfall,
            warmest_year=warmest_year,
            coldest_year=coldest_year,
            warmest_year_mean=warmest_year_mean,
            wettest_year=wettest_year,
            total_records=total_rec,
            valid_records=valid_rec,
            completeness_pct=completeness
        )

climate_service = ClimateProcessingService()
