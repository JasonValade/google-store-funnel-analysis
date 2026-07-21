"""
app.py — V4 dashboard entry point and explicit page router.

Launch command:
    python -m streamlit run dashboard/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Google Store Funnel Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation(
    [
        st.Page(
            "pages/00_executive_overview.py",
            title="Executive Overview",
            icon="🏠",
            default=True,
        ),
        st.Page(
            "pages/01_funnel_trends.py",
            title="Funnel & Conversion Trends",
            icon="📉",
        ),
        st.Page(
            "pages/02_device_product_insights.py",
            title="Device & Product Insights",
            icon="📱",
        ),
        st.Page(
            "pages/03_tracking_health.py",
            title="Tracking Health",
            icon="🔍",
        ),
        st.Page(
            "pages/04_purchase_propensity.py",
            title="Purchase Propensity",
            icon="🤖",
        ),
        st.Page(
            "pages/05_methodology.py",
            title="Methodology & Limitations",
            icon="📋",
        ),
    ]
)

pg.run()
