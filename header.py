"""
Header and Hero Banner Component for EarthScope
"""

import textwrap
from typing import Optional
from earthscope.config import APP_NAME, APP_SUBTITLE, TEAM_NAME, CHALLENGE_TITLE


def render_header_html(
    location_name: str,
    lat: float,
    lon: float,
    api_status: str = "Connected (NASA POWER v2)",
    last_retrieval: Optional[str] = None
) -> str:
    """
    Renders the futuristic space-themed header.
    """
    retrieval_text = f"• Last Sync: {last_retrieval}" if last_retrieval else ""

    html = f"""<div style="
        background: linear-gradient(135deg, rgba(11, 15, 25, 0.95) 0%, rgba(13, 37, 76, 0.85) 50%, rgba(8, 18, 38, 0.95) 100%);
        border: 1px solid rgba(0, 240, 255, 0.25);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0, 240, 255, 0.08), 0 2px 10px rgba(0, 0, 0, 0.5);
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: -50px;
            right: -50px;
            width: 180px;
            height: 180px;
            background: radial-gradient(circle, rgba(0, 240, 255, 0.15) 0%, rgba(0,0,0,0) 70%);
            border-radius: 50%;
            pointer-events: none;
        "></div>

        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
            <div>
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span style="
                        background: linear-gradient(90deg, #00f0ff, #38bdf8);
                        color: #081226;
                        font-size: 11px;
                        font-weight: 800;
                        padding: 3px 10px;
                        border-radius: 9999px;
                        letter-spacing: 0.08em;
                        text-transform: uppercase;
                    ">
                        NASA Space Apps 2026
                    </span>
                    <span style="
                        background: rgba(16, 185, 129, 0.15);
                        border: 1px solid rgba(16, 185, 129, 0.4);
                        color: #10b981;
                        font-size: 11px;
                        font-weight: 600;
                        padding: 3px 10px;
                        border-radius: 9999px;
                    ">
                        Team {TEAM_NAME}
                    </span>
                </div>

                <h1 style="
                    margin: 0 0 6px 0;
                    font-size: 32px;
                    font-weight: 800;
                    letter-spacing: -0.03em;
                    background: linear-gradient(120deg, #ffffff 0%, #cbd5e1 50%, #00f0ff 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-family: 'Space Grotesk', Inter, sans-serif;
                ">
                    {APP_NAME} <span style="font-weight: 300; font-size: 24px; color: #38bdf8;">— {APP_SUBTITLE}</span>
                </h1>

                <p style="margin: 0; color: #94a3b8; font-size: 14px; max-width: 680px; line-height: 1.5;">
                    Investigate planetary environmental shifts with authentic NASA Earth observations,
                    statistically rigorous trend detection, and evidence-grounded scientific insights.
                </p>
            </div>

            <div style="
                background: rgba(15, 23, 42, 0.8);
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 12px 16px;
                min-width: 260px;
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
            ">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <span style="width: 8px; height: 8px; background: #10b981; border-radius: 50%; box-shadow: 0 0 6px #10b981;"></span>
                    <span style="font-size: 11px; color: #cbd5e1; font-weight: 600;">{api_status}</span>
                </div>
                <div style="font-size: 12px; color: #f8fafc; font-weight: 600; margin-bottom: 2px;">
                    📍 {location_name}
                </div>
                <div style="font-size: 11px; color: #64748b; font-family: monospace;">
                    Coords: {lat:.4f}°N, {lon:.4f}°E {retrieval_text}
                </div>
            </div>
        </div>
    </div>"""
    return "\n".join(line.strip() for line in html.strip().splitlines())


