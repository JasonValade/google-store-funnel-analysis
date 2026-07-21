"""
01_funnel_trends.py — Funnel & Conversion Trends page.

Shows weekly purchase conversion rates and the primary ordered funnel
with date-range filtering and downloadable data.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

_DASH = Path(__file__).resolve().parent.parent
if str(_DASH) not in sys.path:
    sys.path.insert(0, str(_DASH))

from utils.data_loader import load_weekly_conversion, load_device_funnel, render_sidebar
from utils.charts import weekly_conversion_chart, funnel_chart

render_sidebar()

st.title("📉 Funnel & Conversion Trends")
st.caption("Primary ordered funnel · Weekly trends · Nov 2020 – Jan 2021")
st.divider()

weekly_df = load_weekly_conversion()
device_df = load_device_funnel()

# ── Date-range filter ─────────────────────────────────────────────────────────
st.subheader("Filters")

# Exclude the partial first week (2020-10-26) by default
full_weeks = weekly_df[weekly_df["week_start"] >= "2020-11-02"].copy()
min_date = full_weeks["week_start"].min().date()
max_date = full_weeks["week_start"].max().date()

col_a, col_b, _ = st.columns([1, 1, 2])
with col_a:
    start_sel = st.date_input("From week", value=min_date, min_value=min_date, max_value=max_date)
with col_b:
    end_sel   = st.date_input("To week",   value=max_date, min_value=min_date, max_value=max_date)

filtered = full_weeks[
    (full_weeks["week_start"].dt.date >= start_sel) &
    (full_weeks["week_start"].dt.date <= end_sel)
].copy()

if filtered.empty:
    st.warning("No weeks match the selected date range. Adjust the filters.")
    st.stop()

st.caption(
    "Note: The week beginning 2020-10-26 is excluded by default because "
    "GA4 data starts 2020-11-01, making that row a partial week (537 sessions)."
)

st.divider()

# ── Weekly conversion trend ───────────────────────────────────────────────────
st.subheader("Weekly Purchase Conversion Rate")

st.plotly_chart(
    weekly_conversion_chart(filtered),
    width="stretch",
    theme="streamlit",
)

# Stage-to-stage metrics for the filtered period
total_views     = int(filtered["product_view_sessions"].sum())
total_checkouts = int(filtered["checkout_sessions"].sum())
total_purchases = int(filtered["purchase_sessions"].sum())

st.caption("Filtered weekly totals for the selected date range.")
mc1, mc2, mc3, mc4, mc5 = st.columns(5)
mc1.metric("Product-view sessions",  f"{total_views:,}")
mc2.metric("Checkout sessions",      f"{total_checkouts:,}")
mc3.metric("Purchase sessions",      f"{total_purchases:,}")
mc4.metric("View → Checkout",        f"{total_checkouts/total_views*100:.2f}%")
mc5.metric("Overall conversion",     f"{total_purchases/total_views*100:.2f}%")

with st.expander("ℹ️ Tracking limitation: Add to cart gap"):
    st.markdown(
        """
        **Add to cart tracking was unreliable across two periods:**

        - **Nov 1–15, 2020**: Add to cart (`add_to_cart`) counts are present but
          depressed vs. expected.
        - **Nov 21–24, 2020**: Add to cart (`add_to_cart`) count = 0 on all four
          days despite normal page-view and Product view traffic — classified as a
          critical tracking outage.

        Because of this, the four-stage clean cart funnel
        (Product view → Add to cart → Begin checkout → Purchase)
        is restricted to the reliable tracking period starting Nov 25, 2020.
        The primary three-stage funnel shown here
        (Product view → Begin checkout → Purchase) is unaffected.

        See the **Tracking Health** page for the full alert timeline.
        """
    )

st.divider()

# ── Primary ordered funnel ────────────────────────────────────────────────────
st.subheader("Full-dataset ordered funnel")
st.caption("Product view → Begin checkout → Purchase · Nov 2020 – Jan 2021 (all devices)")

col_funnel, col_note = st.columns([1, 1])

with col_funnel:
    all_views     = int(device_df["product_view_sessions"].sum())
    all_checkouts = int(device_df["checkout_sessions"].sum())
    all_purchases = int(device_df["purchase_sessions"].sum())

    st.plotly_chart(
        funnel_chart(
            ["Product view", "Begin checkout", "Purchase"],
            [all_views, all_checkouts, all_purchases],
        ),
        width="stretch",
        theme="streamlit",
    )

with col_note:
    st.markdown("#### Stage-to-stage conversion")
    st.markdown(
        f"""
| Stage | Sessions | Conversion |
|---|---:|---:|
| Product view | {all_views:,} | — |
| Begin checkout | {all_checkouts:,} | {all_checkouts/all_views*100:.2f}% (view → checkout) |
| Purchase | {all_purchases:,} | {all_purchases/all_checkouts*100:.2f}% (checkout → purchase) |
| **Overall** | | **{all_purchases/all_views*100:.2f}%** |
        """
    )

    st.markdown("---")
    st.markdown(
        """
        **Clean cart funnel** (restricted to Nov 25 – Jan 31):

        | Stage | Sessions | Rate |
        |---|---:|---:|
        | Product view | 61,835 | — |
        | Add to cart | 15,145 | 24.49% |
        | Begin checkout | 5,292 | 34.94% cart → checkout |
        | Purchase | 2,751 | 51.98% checkout → purchase |
        | **Overall** | | **4.45%** |

        The add-to-cart stage is excluded from the primary funnel due to
        tracking gaps in November 2020.
        """
    )

st.divider()

# ── Download ──────────────────────────────────────────────────────────────────
st.subheader("Download Filtered Weekly Data")

display_cols = [
    "week_start", "product_view_sessions", "checkout_sessions",
    "purchase_sessions", "view_to_checkout_rate",
    "checkout_to_purchase_rate", "purchase_conversion_rate",
]
download_df = filtered[display_cols].copy()
download_df["week_start"] = download_df["week_start"].dt.strftime("%Y-%m-%d")

st.download_button(
    label="⬇️ Download as CSV",
    data=download_df.to_csv(index=False),
    file_name="weekly_conversion_filtered.csv",
    mime="text/csv",
)

st.dataframe(
    download_df.rename(columns={
        "week_start": "Week",
        "product_view_sessions": "Product views",
        "checkout_sessions": "Checkouts",
        "purchase_sessions": "Purchases",
        "view_to_checkout_rate": "View→Checkout %",
        "checkout_to_purchase_rate": "Checkout→Purchase %",
        "purchase_conversion_rate": "Overall rate %",
    }),
    width="stretch",
    hide_index=True,
)
