"""
00_executive_overview.py — Executive Overview page.
"""

import sys
from pathlib import Path

import streamlit as st

_DASH = Path(__file__).resolve().parent.parent
if str(_DASH) not in sys.path:
    sys.path.insert(0, str(_DASH))

from utils.data_loader import (
    load_device_funnel,
    load_weekly_conversion,
    load_model_metrics,
    render_sidebar,
)
from utils.charts import funnel_chart, weekly_conversion_chart

render_sidebar()

st.title("📊 Google Merchandise Store — Conversion Funnel Analysis")
st.caption(
    "Nov 2020 – Jan 2021 · "
    "4.3 M GA4 events · "
    "360 k sessions · "
    "BigQuery public dataset · "
    "**Offline portfolio prototype — no live data**"
)
st.info("Use the sidebar to navigate between dashboard sections.", icon="🧭")
st.divider()

device_df = load_device_funnel()
weekly_df = load_weekly_conversion()
metrics = load_model_metrics()

st.subheader("Key Metrics")
k1, k2, k3, k4 = st.columns(4)

k1.metric(
    label="Product-view sessions",
    value=f"{metrics['dataset_rows']:,}",
    help="Sessions that contained at least one Product view event (model dataset).",
)
k2.metric(
    label="Purchasing sessions",
    value=f"{metrics['dataset_positive_sessions']:,}",
    help="Sessions where a Purchase occurred after the first Product view.",
)
k3.metric(
    label="Session purchase rate",
    value=f"{metrics['overall_positive_rate']*100:.2f}%",
    help="Overall fraction of product-view sessions ending in purchase (model target).",
)
k4.metric(
    label="Top-decile lift (model)",
    value=f"{metrics['test_top_decile_lift']:.2f}×",
    help=(
        "Calibrated Random Forest on the chronological test set. "
        "Top-risk decile purchased at 3.13× the overall test rate. "
        "Associations only — not causal effects."
    ),
)

st.divider()

col_funnel, col_trend = st.columns([1, 2])

with col_funnel:
    st.subheader("Primary Ordered Funnel")
    st.caption("Product view → Begin checkout → Purchase · All devices combined")

    total_views = int(device_df["product_view_sessions"].sum())
    total_checkouts = int(device_df["checkout_sessions"].sum())
    total_purchases = int(device_df["purchase_sessions"].sum())

    st.plotly_chart(
        funnel_chart(
            ["Product view", "Begin checkout", "Purchase"],
            [total_views, total_checkouts, total_purchases],
            title="",
        ),
        width="stretch",
        theme="streamlit",
    )

    v2c = total_checkouts / total_views * 100
    c2p = total_purchases / total_checkouts * 100
    overall = total_purchases / total_views * 100

    m1, m2, m3 = st.columns(3)
    m1.metric("View → Checkout", f"{v2c:.2f}%")
    m2.metric("Checkout → Purchase", f"{c2p:.2f}%")
    m3.metric("Overall conversion", f"{overall:.2f}%")

with col_trend:
    st.subheader("Weekly Purchase Conversion Rate")
    st.caption("Excludes partial week of 2020-10-26")

    weekly_trimmed = weekly_df[weekly_df["week_start"] >= "2020-11-02"].copy()
    st.plotly_chart(
        weekly_conversion_chart(weekly_trimmed),
        width="stretch",
        theme="streamlit",
    )
    st.caption(
        "Peak of **8.93%** during the week of Dec 7, followed by a decline "
        "through January. Add-to-cart tracking was unreliable Nov 1–15 and "
        "unavailable Nov 21–24 — see Tracking Health."
    )

st.divider()
st.subheader("Analysis Versions")
v1, v2, v3 = st.columns(3)

with v1:
    st.markdown("#### V1 · Funnel Analytics")
    st.markdown(
        "- **77,020** product-view sessions analysed  \n"
        "- Primary funnel: **6.05%** overall conversion  \n"
        "- Clean 4-stage cart funnel: **4.45%** (restricted to reliable tracking period)  \n"
        "- Device comparison: mobile 6.26% vs. desktop 5.91%  \n"
        "- Borderline z-test (p = 0.05) — small practical difference  \n"
        "- Product opportunity table: high-view / low-purchase items identified"
    )

with v2:
    st.markdown("#### V2 · Tracking Health")
    st.markdown(
        "- Hybrid GA4 tracking-health monitor  \n"
        "- Detected all **4** validated Add to cart outage dates  \n"
        "- Nov 21–24, 2020: critical tracking outage (event count = 0)  \n"
        "- Dec 19 and Jan 31: likely traffic decline  \n"
        "- Rolling 7-day baseline with traffic-ratio adjustment  \n"
        "- **Offline prototype only** — not a deployed alerting system"
    )

with v3:
    st.markdown("#### V3 · Purchase Propensity Model")
    st.markdown(
        "- Leakage-safe, session-level Random Forest + sigmoid calibration  \n"
        "- Prediction at first Product view; target = session-level Purchase  \n"
        "- Test PR-AUC **0.1402** vs. 0.0504 no-skill (2.8× improvement)  \n"
        "- Top-decile lift **3.13×**, capturing **31.2%** of purchases  \n"
        "- Brier score reduced from 0.1778 → **0.0457** after calibration  \n"
        "- Propensity associations only — **not causal effects**"
    )

st.divider()
st.info(
    "**Offline portfolio prototype** — All analytical results are pre-computed "
    "from local CSV/JSON artifacts. No BigQuery connection, Google credentials, "
    "or live scoring is used in this dashboard.",
    icon="ℹ️",
)
