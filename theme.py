"""
Plotly Theme and Styling Configuration for EarthScope
Space-inspired scientific aesthetic with deep midnight-navy backgrounds,
neon cyan/electric-blue accents, and ultra-legible typography.
"""

from typing import Dict, Any, Optional
import plotly.graph_objects as go

# Color Palette
BG_COLOR = "#081226"          # Deep midnight navy
CARD_BG_COLOR = "#0f172a"     # Dark slate
GRID_COLOR = "#1e293b"        # Subtle slate grid
TEXT_COLOR = "#f8fafc"        # Bright off-white
MUTED_TEXT = "#94a3b8"        # Soft gray
BORDER_COLOR = "#334155"      # Fine border

# Accent Colors
COLOR_CYAN = "#00f0ff"        # Primary temperature / hero
COLOR_SKY = "#38bdf8"         # Secondary blue / min temp
COLOR_EMERALD = "#10b981"     # Precipitation / vegetation
COLOR_AMBER = "#f59e0b"       # Solar irradiance
COLOR_ROSE = "#f43f5e"        # Max temp / extreme heat
COLOR_VIOLET = "#a855f7"      # Skin temp / thermal
COLOR_INDIGO = "#6366f1"      # Comparative baseline

FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


def apply_earthscope_theme(fig: go.Figure, title: str = "", x_title: str = "", y_title: str = "", height: int = 420) -> go.Figure:
    """
    Applies the EarthScope dark scientific styling to a Plotly figure.
    """
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        height=height,
        margin=dict(l=55, r=30, t=55, b=50),
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(family=FONT_FAMILY, size=15, color=TEXT_COLOR),
            x=0.01,
            xanchor="left",
            y=0.96
        ),
        xaxis=dict(
            title=dict(text=x_title, font=dict(family=FONT_FAMILY, size=12, color=MUTED_TEXT)),
            showgrid=True,
            gridcolor=GRID_COLOR,
            gridwidth=0.75,
            zeroline=False,
            tickfont=dict(family=FONT_FAMILY, size=11, color=MUTED_TEXT),
            linecolor=BORDER_COLOR
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(family=FONT_FAMILY, size=12, color=MUTED_TEXT)),
            showgrid=True,
            gridcolor=GRID_COLOR,
            gridwidth=0.75,
            zeroline=False,
            tickfont=dict(family=FONT_FAMILY, size=11, color=MUTED_TEXT),
            linecolor=BORDER_COLOR
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            font=dict(family=FONT_FAMILY, size=11, color=TEXT_COLOR),
            bgcolor="rgba(15, 23, 42, 0.7)",
            bordercolor=BORDER_COLOR,
            borderwidth=1
        ),
        hoverlabel=dict(
            bgcolor="#1e293b",
            font=dict(family=FONT_FAMILY, size=12, color=TEXT_COLOR),
            bordercolor=COLOR_CYAN
        ),
        hovermode="x unified"
    )
    return fig
