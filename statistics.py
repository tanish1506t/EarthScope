"""
Statistical Analysis and Trend Service
Implements OLS linear regression with confidence intervals, non-parametric Mann-Kendall,
Sen's slope median estimator, and distribution histograms.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from scipy import stats

from backend.app.config import PARAMETERS_META
from backend.app.schemas import DescriptiveStatistics, HistogramBin, TrendResult

class StatisticsService:
    @staticmethod
    def calculate_descriptive_stats(series: pd.Series, var_name: str) -> DescriptiveStatistics:
        clean = series.dropna()
        total_len = len(series)
        valid_len = len(clean)
        meta = PARAMETERS_META.get(var_name.upper(), {})
        units = meta.get("units", "")

        if valid_len == 0:
            return DescriptiveStatistics(
                variable=var_name,
                units=units,
                total_records=total_len,
                valid_observations=0,
                missing_pct=100.0
            )

        mean_val = float(clean.mean())
        median_val = float(clean.median())
        std_val = float(clean.std(ddof=1)) if valid_len > 1 else 0.0
        min_val = float(clean.min())
        max_val = float(clean.max())

        q25, q75 = np.percentile(clean, [25, 75])
        p10, p90 = np.percentile(clean, [10, 90])
        iqr_val = float(q75 - q25)

        skew_val = float(stats.skew(clean)) if valid_len > 2 else 0.0
        kurt_val = float(stats.kurtosis(clean)) if valid_len > 3 else 0.0

        # Construct histogram bins (10 equal bins)
        bins_data: List[HistogramBin] = []
        if max_val > min_val:
            num_bins = min(12, max(6, int(np.sqrt(valid_len))))
            counts, bin_edges = np.histogram(clean, bins=num_bins)
            for i in range(len(counts)):
                b_start = round(float(bin_edges[i]), 2)
                b_end = round(float(bin_edges[i+1]), 2)
                bins_data.append(HistogramBin(
                    bin_start=b_start,
                    bin_end=b_end,
                    label=f"{b_start}–{b_end} {units}",
                    count=int(counts[i])
                ))

        return DescriptiveStatistics(
            variable=var_name,
            units=units,
            total_records=total_len,
            valid_observations=valid_len,
            missing_pct=round((total_len - valid_len) / total_len * 100.0, 1) if total_len > 0 else 0.0,
            mean=round(mean_val, 2),
            median=round(median_val, 2),
            std=round(std_val, 2),
            min=round(min_val, 2),
            max=round(max_val, 2),
            q25=round(float(q25), 2),
            q75=round(float(q75), 2),
            iqr=round(iqr_val, 2),
            p10=round(float(p10), 2),
            p90=round(float(p90), 2),
            skewness=round(skew_val, 3),
            kurtosis=round(kurt_val, 3),
            histogram=bins_data
        )

    @staticmethod
    def calculate_trend(df: pd.DataFrame, parameter: str, temporal_group: str = "yearly") -> TrendResult:
        """
        Calculates linear regression (OLS) and Mann-Kendall trend test.
        temporal_group: 'yearly' (annual aggregate) or 'monthly' (raw time series).
        """
        meta = PARAMETERS_META.get(parameter.upper(), {})
        units = meta.get("units", "")
        param_name = meta.get("name", parameter)

        if df.empty or parameter.lower() not in df.columns:
            return TrendResult(
                parameter=parameter,
                parameter_name=param_name,
                units=units,
                n_observations=0,
                direction="insufficient_data",
                is_significant=False,
                verdict="Insufficient data for trend computation."
            )

        col = parameter.lower()
        if temporal_group == "yearly":
            # For precipitation sum, for others mean
            agg_type = meta.get("agg_method", "mean")
            if agg_type == "sum" or col == "prectotcorr":
                # Only include years with at least 10 valid months
                counts = df.groupby("year")[col].count()
                good_years = counts[counts >= 10].index
                sub = df[df["year"].isin(good_years)]
                grouped = sub.groupby("year")[col].sum().dropna()
            else:
                grouped = df.groupby("year")[col].mean().dropna()

            if len(grouped) < 3:
                return TrendResult(
                    parameter=parameter,
                    parameter_name=param_name,
                    units=units,
                    n_observations=len(grouped),
                    direction="insufficient_data",
                    is_significant=False,
                    verdict="At least 3 valid years required for annual regression."
                )

            x_years = np.array(grouped.index, dtype=float)
            x_labels = [str(int(y)) for y in grouped.index]
            y = grouped.values.astype(float)
            x = x_years - x_years[0]  # Start at t=0
        else:
            clean_s = df[col].dropna()
            if len(clean_s) < 12:
                return TrendResult(
                    parameter=parameter,
                    parameter_name=param_name,
                    units=units,
                    n_observations=len(clean_s),
                    direction="insufficient_data",
                    is_significant=False,
                    verdict="At least 12 monthly records required."
                )
            x_labels = [str(d) for d in clean_s.index.strftime("%Y-%m")]
            y = clean_s.values.astype(float)
            x = np.arange(len(y), dtype=float)

        n = len(y)
        slope, intercept, r_val, p_val, std_err = stats.linregress(x, y)
        r_squared = float(r_val ** 2)

        # 95% confidence intervals on slope
        df_deg = max(1, n - 2)
        t_crit = float(stats.t.ppf(0.975, df_deg))
        ci_lower = slope - t_crit * std_err
        ci_upper = slope + t_crit * std_err

        y_fitted = intercept + slope * x
        residuals = y - y_fitted
        s_err = np.sqrt(np.sum(residuals ** 2) / df_deg)
        x_mean = np.mean(x)
        ss_x = np.sum((x - x_mean) ** 2)
        ci_bands = t_crit * s_err * np.sqrt(1.0 / n + (x - x_mean) ** 2 / (ss_x if ss_x > 0 else 1.0))

        # Mann-Kendall test
        mk_z, mk_p, sens_slope = StatisticsService._mann_kendall(y)

        # Scale slope
        if temporal_group == "yearly":
            slope_yr = slope
            slope_dec = slope * 10.0
            tot_change = slope * (len(x) - 1)
        else:
            slope_yr = slope * 12.0
            slope_dec = slope * 120.0
            tot_change = slope * (len(x) - 1)

        is_sig = bool(p_val < 0.05)
        if slope > 0.001:
            direction = "warming" if "temp" in param_name.lower() or "t2m" in col else "increasing"
        elif slope < -0.001:
            direction = "cooling" if "temp" in param_name.lower() or "t2m" in col else "decreasing"
        else:
            direction = "stable"

        if is_sig:
            verdict = f"Statistically significant {direction} trend (p = {p_val:.4f} < 0.05, R² = {r_squared:.3f})."
        else:
            verdict = f"No statistically significant monotonic trend detected (p = {p_val:.4f} ≥ 0.05, R² = {r_squared:.3f})."

        return TrendResult(
            parameter=parameter,
            parameter_name=param_name,
            units=units,
            n_observations=n,
            slope_per_year=round(float(slope_yr), 4),
            slope_per_decade=round(float(slope_dec), 4),
            intercept=round(float(intercept), 3),
            r_squared=round(float(r_squared), 4),
            p_value=round(float(p_val), 5),
            std_error=round(float(std_err), 5),
            ci_95_lower=round(float(ci_lower), 4),
            ci_95_upper=round(float(ci_upper), 4),
            total_change_over_period=round(float(tot_change), 2),
            direction=direction,
            is_significant=is_sig,
            mann_kendall_z=round(float(mk_z), 3) if mk_z is not None else None,
            mann_kendall_p=round(float(mk_p), 4) if mk_p is not None else None,
            sens_slope=round(float(sens_slope), 4) if sens_slope is not None else None,
            verdict=verdict,
            x_labels=x_labels,
            y_actual=[round(float(v), 2) for v in y],
            y_fitted=[round(float(v), 2) for v in y_fitted],
            ci_lower_band=[round(float(y_fitted[i] - ci_bands[i]), 2) for i in range(n)],
            ci_upper_band=[round(float(y_fitted[i] + ci_bands[i]), 2) for i in range(n)]
        )

    @staticmethod
    def _mann_kendall(y: np.ndarray) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        n = len(y)
        if n < 5:
            return None, None, None

        row_idx, col_idx = np.triu_indices(n, k=1)
        pair_diffs = y[col_idx] - y[row_idx]
        s = np.sum(np.sign(pair_diffs))

        unique_vals, counts = np.unique(y, return_counts=True)
        tied_sum = np.sum(counts * (counts - 1) * (2 * counts + 5))
        var_s = (n * (n - 1) * (2 * n + 5) - tied_sum) / 18.0

        if var_s <= 0:
            z = 0.0
            p_val = 1.0
        else:
            if s > 0:
                z = (s - 1) / np.sqrt(var_s)
            elif s < 0:
                z = (s + 1) / np.sqrt(var_s)
            else:
                z = 0.0
            p_val = 2.0 * (1.0 - stats.norm.cdf(abs(z)))

        time_diffs = (col_idx - row_idx).astype(float)
        pairwise_slopes = pair_diffs / time_diffs
        sens_slope = float(np.median(pairwise_slopes))

        return float(z), float(p_val), float(sens_slope)

statistics_service = StatisticsService()
