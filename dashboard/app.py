"""
app.py — V4 dashboard entry point and explicit page router.

Launch command:
    python -m streamlit run dashboard/app.py
"""

from pathlib import Path

import streamlit as st


def main() -> None:
    st.set_page_config(
        page_title="Google Store Funnel Analysis",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    base_dir = Path(__file__).resolve().parent
    pages = [
        st.Page(
            base_dir / "pages" / "00_executive_overview.py",
            title="Executive Overview",
            icon="🏠",
            default=True,
        ),
        st.Page(
            base_dir / "pages" / "01_funnel_trends.py",
            title="Funnel & Conversion Trends",
            icon="📉",
        ),
        st.Page(
            base_dir / "pages" / "02_device_product_insights.py",
            title="Device & Product Insights",
            icon="📱",
        ),
        st.Page(
            base_dir / "pages" / "03_tracking_health.py",
            title="Tracking Health",
            icon="🔍",
        ),
        st.Page(
            base_dir / "pages" / "04_purchase_propensity.py",
            title="Purchase Propensity",
            icon="🤖",
        ),
        st.Page(
            base_dir / "pages" / "07_roi_calculator.py",
            title="ROI Calculator",
            icon="💰",
        ),
        st.Page(
            base_dir / "pages" / "08_time_series_forecasting.py",
            title="Time-Series Forecasting",
            icon="📈",
        ),
        st.Page(
            base_dir / "pages" / "05_methodology.py",
            title="Methodology & Limitations",
            icon="📋",
        ),
        st.Page(
            base_dir / "pages" / "06_analysis_journey.py",
            title="Analysis Journey",
            icon="🧭",
        ),
    ]
    navigation = st.navigation(pages)
    navigation.run()


if __name__ == "__main__":
    main()
