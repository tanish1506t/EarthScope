"""
Interactive Scientific Charts Module
Builds responsive, feature-rich Plotly figures for EarthScope data investigation.
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from earthscope.config import PARAMETERS_META
from earthscope.visualizations.theme import (
    apply_earthscope_theme,
    COLOR_CYAN,
    COLOR_SKY,
    COLOR_EMERALD,
    COLOR_AMBER,
    COLOR_ROSE,
    COLOR_VIOLET,
    COLOR_INDIGO,
    MUTED_TEXT,
    GRID_COLOR,
    TEXT_COLOR
)
from earthscope.analysis.trend_analysis import linear_regression_trend


def plot_timeseries_with_trend(
    df: pd.DataFrame,
    var_name: str,
    show_rolling: bool = True,
    show_trend: bool = True,
    show_ci: bool = True,
    rolling_window: int = 30
) -> go.Figure:
    """
    Primary time series plot showing actual data, rolling mean, OLS trend line, and 95% CI band.
    """
    fig = go.Figure()

    if df.empty or var_name not in df.columns:
        fig.add_annotation(text="No data available for the selected parameters", showarrow=False, font=dict(size=14, color=MUTED_TEXT))
        return apply_earthscope_theme(fig, "Time Series")

    meta = PARAMETERS_META.get(var_name, {})
    units = meta.get("units", "")
    readable_name = meta.get("name", var_name)
    primary_color = meta.get("color", COLOR_CYAN)

    series = df[var_name].dropna()
    if series.empty:
        fig.add_annotation(text="All observations in selected range are missing (NaN)", showarrow=False, font=dict(size=14, color=MUTED_TEXT))
        return apply_earthscope_theme(fig, readable_name)

    # 1. Raw Observations
    fig.add_trace(go.Scatter(
        x=series.index,
        y=series.values,
        mode="lines",
        name="Observations",
        line=dict(color="rgba(148, 163, 184, 0.4)", width=1.0),
        hovertemplate="%{x|%Y-%m-%d}<br>Observed: <b>%{y:.2f} " + units + "</b><extra></extra>"
    ))

    # 2. Rolling Average
    if show_rolling and len(series) >= rolling_window:
        roll_s = series.rolling(window=rolling_window, min_periods=max(3, rolling_window // 3)).mean()
        fig.add_trace(go.Scatter(
            x=roll_s.index,
            y=roll_s.values,
            mode="lines",
            name=f"{rolling_window}-Day Moving Avg",
            line=dict(color=primary_color, width=2.5),
            hovertemplate="%{x|%Y-%m-%d}<br>" + f"{rolling_window}d Avg: <b>" + "%{y:.2f} " + units + "</b><extra></extra>"
        ))

    # 3. OLS Trend Line & 95% Confidence Interval
    if show_trend and len(series) >= 10:
        reg = linear_regression_trend(series)
        if reg.get("status") == "success":
            x_dates = series.index
            y_trend = reg["y_fitted"]
            y_lower = reg["ci_lower_band"]
            y_upper = reg["ci_upper_band"]

            # Confidence interval ribbon
            if show_ci:
                fig.add_trace(go.Scatter(
                    x=x_dates,
                    y=y_upper,
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo="skip"
                ))
                fig.add_trace(go.Scatter(
                    x=x_dates,
                    y=y_lower,
                    mode="lines",
                    line=dict(width=0),
                    fill="tonexty",
                    fillcolor="rgba(245, 158, 11, 0.15)",
                    name="95% Confidence Band",
                    hoverinfo="skip"
                ))

            # Linear trend line
            trend_label = f"Trend ({reg['slope_per_decade']:+.2f} {units}/decade, p={reg['p_value']:.3f})"
            fig.add_trace(go.Scatter(
                x=x_dates,
                y=y_trend,
                mode="lines",
                name=trend_label,
                line=dict(color=COLOR_AMBER, width=2.2, dash="dash"),
                hovertemplate="%{x|%Y-%m-%d}<br>Trend: <b>%{y:.2f} " + units + "</b><extra></extra>"
            ))

    title = f"{readable_name} Time Series & Empirical Trend"
    return apply_earthscope_theme(fig, title=title, x_title="Date", y_title=f"{readable_name} ({units})")


def plot_temperature_envelope(df: pd.DataFrame) -> go.Figure:
    """
    Renders diurnal temperature envelope: T2M_MIN to T2M_MAX ribbon with T2M mean line.
    """
    fig = go.Figure()

    if df.empty or "T2M" not in df.columns:
        fig.add_annotation(text="Temperature parameters (T2M, T2M_MIN, T2M_MAX) unavailable", showarrow=False)
        return apply_earthscope_theme(fig, "Diurnal Temperature Envelope")

    t_mean = df["T2M"].dropna()
    has_min = "T2M_MIN" in df.columns
    has_max = "T2M_MAX" in df.columns

    if has_max and has_min:
        t_min = df["T2M_MIN"].dropna()
        t_max = df["T2M_MAX"].dropna()
        common_idx = t_mean.index.intersection(t_min.index).intersection(t_max.index)

        # Upper boundary
        fig.add_trace(go.Scatter(
            x=common_idx,
            y=t_max.loc[common_idx],
            mode="lines",
            name="Max Temp (T2M_MAX)",
            line=dict(color=COLOR_ROSE, width=1.0),
            hovertemplate="%{x|%Y-%m-%d}<br>Max: <b>%{y:.1f} °C</b><extra></extra>"
        ))

        # Lower boundary with ribbon fill
        fig.add_trace(go.Scatter(
            x=common_idx,
            y=t_min.loc[common_idx],
            mode="lines",
            name="Min Temp (T2M_MIN)",
            line=dict(color=COLOR_SKY, width=1.0),
            fill="tonexty",
            fillcolor="rgba(56, 189, 248, 0.15)",
            hovertemplate="%{x|%Y-%m-%d}<br>Min: <b>%{y:.1f} °C</b><extra></extra>"
        ))

    # Mean temperature curve
    fig.add_trace(go.Scatter(
        x=t_mean.index,
        y=t_mean.values,
        mode="lines",
        name="Mean Temp (T2M)",
        line=dict(color=COLOR_CYAN, width=2.0),
        hovertemplate="%{x|%Y-%m-%d}<br>Mean: <b>%{y:.1f} °C</b><extra></extra>"
    ))

    return apply_earthscope_theme(
        fig,
        title="Surface Air Temperature Envelope (Daily Mean, Min & Max Range)",
        x_title="Date",
        y_title="Temperature (°C)"
    )


def plot_precipitation_analysis(df: pd.DataFrame, monthly_df: Optional[pd.DataFrame] = None) -> go.Figure:
    """
    Renders precipitation investigation: daily rainfall bars and cumulative mass curves.
    """
    if df.empty or "PRECTOTCORR" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Precipitation data (PRECTOTCORR) unavailable", showarrow=False)
        return apply_earthscope_theme(fig, "Precipitation Analysis")

    p_daily = df["PRECTOTCORR"].dropna()

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("Daily Precipitation Events (mm/day)", "Annual Cumulative Rainfall Accumulation (mm)")
    )

    # 1. Daily Precipitation Bars
    fig.add_trace(
        go.Bar(
            x=p_daily.index,
            y=p_daily.values,
            name="Daily Rainfall",
            marker=dict(color=COLOR_EMERALD, opacity=0.8),
            hovertemplate="%{x|%Y-%m-%d}<br>Rainfall: <b>%{y:.1f} mm</b><extra></extra>"
        ),
        row=1, col=1
    )

    # 2. Cumulative sum by year
    df_cum = df[["PRECTOTCORR"]].copy()
    df_cum["year"] = df_cum.index.year
    df_cum["cum_rain"] = df_cum.groupby("year")["PRECTOTCORR"].cumsum()

    fig.add_trace(
        go.Scatter(
            x=df_cum.index,
            y=df_cum["cum_rain"],
            mode="lines",
            name="Cumulative Annual Rain",
            line=dict(color=COLOR_CYAN, width=2.0),
            hovertemplate="%{x|%Y-%m-%d}<br>Cumulative: <b>%{y:.1f} mm</b><extra></extra>"
        ),
        row=2, col=1
    )

    fig = apply_earthscope_theme(fig, "Precipitation Dynamics & Cumulative Accumulation", height=500)
    fig.update_layout(showlegend=True)
    return fig


def plot_monthly_climatology(clim_df: pd.DataFrame, var_name: str) -> go.Figure:
    """
    Renders the 12-month annual climatological cycle with standard deviation bands.
    """
    fig = go.Figure()
    if clim_df.empty or var_name not in clim_df.columns:
        fig.add_annotation(text="Climatology data unavailable", showarrow=False)
        return apply_earthscope_theme(fig, "Annual Climatological Cycle")

    meta = PARAMETERS_META.get(var_name, {})
    units = meta.get("units", "")
    readable_name = meta.get("name", var_name)
    color = meta.get("color", COLOR_CYAN)

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    x_axis = [months[m - 1] for m in clim_df.index]
    y_vals = clim_df[var_name]

    # Check for std
    std_col = f"{var_name}_std"
    if std_col in clim_df.columns:
        y_std = clim_df[std_col].fillna(0)
        fig.add_trace(go.Bar(
            x=x_axis,
            y=y_vals,
            error_y=dict(type="data", array=y_std.values, visible=True, color="rgba(248, 250, 252, 0.4)"),
            marker=dict(color=color, opacity=0.85),
            name="Monthly Normal (±1σ)",
            hovertemplate="%{x}<br>Normal: <b>%{y:.2f} " + units + "</b> (±%{error_y.array:.2f})<extra></extra>"
        ))
    else:
        fig.add_trace(go.Bar(
            x=x_axis,
            y=y_vals,
            marker=dict(color=color, opacity=0.85),
            name="Monthly Normal",
            hovertemplate="%{x}<br>Normal: <b>%{y:.2f} " + units + "</b><extra></extra>"
        ))

    return apply_earthscope_theme(
        fig,
        title=f"12-Month Climatological Cycle: {readable_name}",
        x_title="Calendar Month",
        y_title=f"{readable_name} ({units})"
    )


def plot_monthly_anomalies(anomaly_df: pd.DataFrame, var_name: str) -> go.Figure:
    """
    Diverging red/blue anomaly bar chart relative to baseline normals.
    """
    fig = go.Figure()
    anom_col = f"{var_name}_anomaly"

    if anomaly_df.empty or anom_col not in anomaly_df.columns:
        fig.add_annotation(text="Anomaly records unavailable", showarrow=False)
        return apply_earthscope_theme(fig, "Monthly Anomalies")

    meta = PARAMETERS_META.get(var_name, {})
    units = meta.get("units", "")
    readable_name = meta.get("name", var_name)

    clean_anom = anomaly_df[anom_col].dropna()
    # Colors: positive -> rose/amber, negative -> sky/blue
    colors = [COLOR_ROSE if v >= 0 else COLOR_SKY for v in clean_anom.values]

    fig.add_trace(go.Bar(
        x=clean_anom.index,
        y=clean_anom.values,
        marker=dict(color=colors),
        name="Monthly Anomaly",
        hovertemplate="%{x|%Y-%m}<br>Anomaly: <b>%{y:+.2f} " + units + "</b><extra></extra>"
    ))

    # Add 0 baseline
    fig.add_hline(y=0.0, line_dash="dash", line_color=MUTED_TEXT, line_width=1.0)

    return apply_earthscope_theme(
        fig,
        title=f"Monthly Departure from Climatological Normal: {readable_name}",
        x_title="Month",
        y_title=f"Anomaly ({units})"
    )


def plot_distribution_histogram(series: pd.Series, var_name: str) -> go.Figure:
    """
    Histogram and distribution curve with mean and median indicators.
    """
    fig = go.Figure()
    clean_s = series.dropna()

    if clean_s.empty:
        fig.add_annotation(text="No valid values to plot distribution", showarrow=False)
        return apply_earthscope_theme(fig, "Distribution Analysis")

    meta = PARAMETERS_META.get(var_name, {})
    units = meta.get("units", "")
    readable_name = meta.get("name", var_name)
    color = meta.get("color", COLOR_CYAN)

    mean_v = float(clean_s.mean())
    median_v = float(clean_s.median())

    fig.add_trace(go.Histogram(
        x=clean_s.values,
        nbinsx=40,
        marker=dict(color=color, opacity=0.7, line=dict(color=BG_COLOR, width=1)),
        name="Frequency",
        hovertemplate="Bin: %{x} " + units + "<br>Count: %{y}<extra></extra>"
    ))

    fig.add_vline(x=mean_v, line_dash="dash", line_color=COLOR_AMBER, line_width=2,
                  annotation_text=f"Mean: {mean_v:.2f}", annotation_position="top right")
    fig.add_vline(x=median_v, line_dash="dot", line_color=COLOR_ROSE, line_width=2,
                  annotation_text=f"Median: {median_v:.2f}", annotation_position="top left")

    return apply_earthscope_theme(
        fig,
        title=f"Distribution of {readable_name}",
        x_title=f"{readable_name} ({units})",
        y_title="Observation Count"
    )
