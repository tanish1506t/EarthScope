"""
About CodeRex and Project Overview Page for EarthScope
"""

import streamlit as st
from earthscope.config import APP_NAME, APP_SUBTITLE, TEAM_NAME, CHALLENGE_TITLE


def render_about_page() -> None:
    """
    Renders the About CodeRex and Project Overview page.
    """
    st.markdown("### 👥 About Team CodeRex & Project EarthScope")

    st.html(f"""
    <div style="
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(8, 18, 38, 0.95) 100%);
        border: 1px solid rgba(0, 240, 255, 0.3);
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 24px;
    ">
        <h2 style="color: #00f0ff; margin-top: 0; font-size: 24px;">{APP_NAME} — {APP_SUBTITLE}</h2>
        <div style="font-size: 13px; color: #38bdf8; font-weight: 600; margin-bottom: 12px;">
            {CHALLENGE_TITLE}
        </div>
        <p style="font-size: 14px; color: #e2e8f0; line-height: 1.6;">
            EarthScope is an advanced, fully functional environmental analytics platform created by <strong>Team CodeRex</strong>.
            Our mission is to empower students, scientists, educators, and citizens to become genuine <em>Earth System Trend Detectives</em>.
            By democratizing access to authentic NASA satellite observations and coupling them with rigorous statistical analytics,
            EarthScope replaces speculative headlines with reproducible, evidence-grounded scientific insights.
        </p>
    </div>
    """)

    c_team, c_tech = st.columns([1.1, 1.3])

    with c_team:
        st.markdown("#### 🚀 Team CodeRex")
        st.html("""
        <div style="background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 18px; font-size: 13px; color: #cbd5e1; line-height: 1.6;">
            <div style="font-weight: 700; color: #10b981; font-size: 16px; margin-bottom: 6px;">Team CodeRex</div>
            <div style="font-size: 12px; color: #94a3b8; margin-bottom: 12px;">
                Passionate developers, data scientists, and Earth science enthusiasts participating in the NASA Space Apps Challenge 2026.
            </div>
            <strong>Core Competencies:</strong><br>
            • Full-Stack Python & Scientific UI/UX<br>
            • Geospatial Data Engineering & NASA APIs<br>
            • Non-Parametric Statistics & Climatology<br>
            • Evidence-Grounded AI Synthesis
        </div>
        """)

        st.markdown("#### 🌟 Scientific Motivation")
        st.markdown("""
        Planetary environmental shifts are often presented through over-simplified or alarming soundbites.
        Our motivation was to build a tool that demonstrates the actual scientific method:
        retrieving raw NASA data, checking observational gaps, testing hypothesis significance,
        and communicating boundaries clearly.
        """)

    with c_tech:
        st.markdown("#### 💻 Technology Architecture")
        tech_data = {
            "Layer": ["Core UI Framework", "Interactive Visualizations", "3D Hero Graphics", "Data Processing", "Statistical Engine", "NASA Data Pipeline", "Geospatial Mapping"],
            "Technologies Used": [
                "Streamlit with Custom CSS & Glassmorphism",
                "Plotly Dark Scientific Theme",
                "Three.js WebGL (Interactive rotating 3D Earth)",
                "Pandas & NumPy",
                "SciPy (Linear Regression, Mann-Kendall, Sen's Slope)",
                "NASA POWER REST API v2 + Local SHA-256 Cache",
                "Plotly Scattergeo & Natural Earth Projection"
            ]
        }
        import pandas as pd
        st.dataframe(pd.DataFrame(tech_data), hide_index=True)

        st.markdown("#### 🤝 Credits & Acknowledgments")
        st.markdown("""
        - **NASA Langley Research Center (LaRC):** For maintaining the open POWER project.
        - **NASA Space Apps Challenge 2026 Organizers:** For the inspiring challenge: *“Be An Earth System Trend Detective!”*
        - **Open-Source Scientific Python Ecosystem:** NumPy, SciPy, Pandas, Plotly, Streamlit, and Three.js.
        """)

    st.markdown("---")

    # Official Disclaimer
    st.html("""
    <div style="
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        font-size: 12px;
        color: #94a3b8;
        line-height: 1.5;
    ">
        <strong>⚖️ Official NASA Space Apps Challenge Disclaimer:</strong><br>
        EarthScope is an independent educational and research project created by Team CodeRex for the NASA Space Apps Challenge 2026.
        It is not an official product or endorsement of the National Aeronautics and Space Administration (NASA) or any other governmental agency.
        All data is ingested from publicly accessible scientific repositories.
    </div>
    """)
