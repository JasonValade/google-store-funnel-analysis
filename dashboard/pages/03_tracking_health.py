"""
03_tracking_health.py — Tracking Health page.

Displays the GA4 event-tracking health monitor results from the offline
prototype. Shows critical outages and likely traffic declines detected by the
hybrid rolling-baseline algorithm.

This is an offline prototype — not a live alerting system.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

_DASH = Path(__file__).resolve().parent.parent
if str(_DASH) not in sys.path:
    sys.path.insert(0, str(_DASH))

from utils.data_loader import load_tracking_alerts, render_sidebar
from utils.charts import tracking_scatter

render_sidebar()

st.title("🔍 Tracking Health Monitor")
st.caption(
    "Hybrid GA4 tracking-health monitor · Nov 2020 – Jan 2021 · "
    "**Offline prototype — not a deployed alerting service**"
)
st.divider()

alerts_df = load_tracking_alerts()
EVENT_LABELS = {
    "add_to_cart": "Add to cart",
    "view_item": "Product view",
}
STATUS_LABELS = {
    "CRITICAL_TRACKING_OUTAGE": "Critical tracking outage",
    "LIKELY_TRAFFIC_DECLINE": "Likely traffic decline",
}

alerts_df["event_label"] = alerts_df["event_name"].map(EVENT_LABELS).fillna(alerts_df["event_name"])
alerts_df["status_label"] = alerts_df["tracking_status"].map(STATUS_LABELS).fillna(alerts_df["tracking_status"])

# ── KPI cards ─────────────────────────────────────────────────────────────────
st.subheader("Alert Summary")

n_critical  = int((alerts_df["tracking_status"] == "CRITICAL_TRACKING_OUTAGE").sum())
n_likely    = int((alerts_df["tracking_status"] == "LIKELY_TRAFFIC_DECLINE").sum())
n_total     = len(alerts_df)
n_events    = alerts_df["event_name"].nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Critical tracking outages", n_critical,
          help="event_count = 0 while page-view traffic was normal.")
k2.metric("Likely traffic declines",   n_likely,
          help="Event ratio low but consistent with a site-wide traffic drop.")
k3.metric("Affected dates",            n_total)
k4.metric("Distinct events affected",  n_events)

st.divider()

# ── Filters ───────────────────────────────────────────────────────────────────
with st.expander("🔍 Filters", expanded=True):
    fa1, fa2 = st.columns(2)

    with fa1:
        event_opts = ["All events"] + sorted(alerts_df["event_label"].unique().tolist())
        event_sel  = st.selectbox("Event name", event_opts)

    with fa2:
        status_opts = ["All statuses"] + sorted(alerts_df["status_label"].unique().tolist())
        status_sel  = st.selectbox("Tracking status", status_opts)

filtered = alerts_df.copy()
if event_sel != "All events":
    filtered = filtered[filtered["event_label"] == event_sel]
if status_sel != "All statuses":
    filtered = filtered[filtered["status_label"] == status_sel]

if filtered.empty:
    st.warning("No alerts match the current filters. Adjust the selections above.")
    st.stop()

# ── Scatter plot ──────────────────────────────────────────────────────────────
st.subheader("Alert Ratios by Date")
st.caption(
    "Dates are categorical on the x-axis — non-consecutive dates are not connected. "
    "Ratio of 1.0 = expected baseline. "
    "Critical outages have event-volume ratio = 0."
)

st.plotly_chart(tracking_scatter(filtered), width="stretch", theme="streamlit")

with st.expander("ℹ️ How the ratios are computed"):
    st.markdown(
        """
        **Rolling 7-day baseline** (excluding the alert date itself):
        - `expected_event_count` = rolling mean of the same event over the previous 7 days
        - `event_volume_ratio` = `event_count / expected_event_count`
        - `page_view_ratio` = `page_view_count / expected_page_view_count`

        **Traffic adjustment:**
        - `traffic_adjusted_event_ratio` = `event_volume_ratio / page_view_ratio`
        - A value near 1.0 means the event changed roughly in line with overall traffic.
        - A value substantially below 1.0 indicates an event-specific decline relative
          to traffic.
        - A value of 0 while page-view traffic persists supports a critical
          tracking-outage classification.

        **Classification rules:**
        - `CRITICAL_TRACKING_OUTAGE`: event count is zero while sufficient page-view
          traffic persists.
        - `LIKELY_TRAFFIC_DECLINE`: raw event ratio is low but traffic-adjusted ratio
          remains near 1.0, suggesting a site-wide traffic decline rather than an
          event-specific failure.
        """
    )

st.divider()

# ── Alert detail table ────────────────────────────────────────────────────────
st.subheader("Alert Detail Table")

display_df = filtered.copy()
display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")

# Format ratio columns to 3 d.p.
ratio_cols = [
    "event_volume_ratio", "page_view_ratio", "traffic_adjusted_event_ratio"
]
for col in ratio_cols:
    display_df[col] = display_df[col].round(3)

display_df = display_df.rename(columns={
    "date":                          "Date",
    "event_label":                   "Event",
    "event_count":                   "Observed",
    "expected_event_count":          "Expected",
    "event_volume_ratio":            "Event ratio",
    "event_volume_z_score":          "Z-score",
    "page_view_count":               "Page views",
    "expected_page_view_count":      "Expected PV",
    "page_view_ratio":               "PV ratio",
    "traffic_adjusted_event_ratio":  "Traffic-adjusted ratio",
    "status_label":                  "Status",
})

display_df = display_df[
    [
        "Date", "Event", "Status", "Observed", "Expected", "Event ratio",
        "Page views", "Expected PV", "PV ratio", "Traffic-adjusted ratio", "Z-score",
    ]
]
for col in ["Observed", "Expected", "Page views", "Expected PV"]:
    display_df[col] = display_df[col].astype(float).round(0).astype(int)

st.dataframe(
    display_df,
    width="stretch",
    hide_index=True,
    column_config={
        "Observed": st.column_config.NumberColumn(format="%,d"),
        "Expected": st.column_config.NumberColumn(format="%,d"),
        "Page views": st.column_config.NumberColumn(format="%,d"),
        "Expected PV": st.column_config.NumberColumn(format="%,d"),
        "Event ratio": st.column_config.NumberColumn(format="%.3f"),
        "PV ratio": st.column_config.NumberColumn(format="%.3f"),
        "Traffic-adjusted ratio": st.column_config.NumberColumn(format="%.3f"),
        "Z-score": st.column_config.NumberColumn(format="%.2f"),
    },
)

st.divider()

# ── Interpretation ────────────────────────────────────────────────────────────
st.subheader("Key Findings")

st.markdown(
    """
    **Critical outages — Nov 21–24, 2020 (Add to cart, 4 days):**
    - Add to cart event count was **zero** on all four dates.
    - Page-view traffic was normal (page-view ratios 0.75–1.23), ruling out a
      site-wide outage.
    - Traffic-adjusted event ratio = 0 → confirmed tracking failure, not traffic decline.
    - These four dates are excluded from the clean four-stage cart funnel.

    **Likely traffic declines — Dec 19, 2020 and Jan 31, 2021:**
    - Product view (Dec 19): traffic-adjusted ratio = **0.860** — event ratio is low
      but page-view ratio is also low (0.601), suggesting a site-wide traffic drop.
    - Add to cart (Jan 31): traffic-adjusted ratio = **0.903** — same pattern.
    - Neither is classified as a tracking failure; both are consistent with
      reduced overall site traffic.
    """
)

st.info(
    "**Prototype disclaimer:** This monitor was built for portfolio demonstration "
    "using offline BigQuery exports. It is not connected to a live GA4 stream "
    "and does not send alerts. Deploying a production monitoring system would "
    "require a real-time event pipeline, alerting infrastructure, and "
    "ongoing threshold calibration.",
    icon="⚠️",
)
