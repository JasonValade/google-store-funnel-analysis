"""
02_device_product_insights.py — Device & Product Insights page.

Compares conversion rates by device and surfaces high-traffic / low-purchase
product candidates from the session-level model feature file.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

_DASH = Path(__file__).resolve().parent.parent
if str(_DASH) not in sys.path:
    sys.path.insert(0, str(_DASH))

from utils.data_loader import load_device_funnel, load_model_features, render_sidebar
from utils.charts import device_bar_chart

render_sidebar()

st.title("📱 Device & Product Insights")
st.caption(
    "Device conversion comparison · Product-opportunity candidates · Nov 2020 – Jan 2021"
)
st.divider()

device_df   = load_device_funnel()
features_df = load_model_features()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Device comparison
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("Device Conversion Rates")

st.plotly_chart(device_bar_chart(device_df), width="stretch", theme="streamlit")

display = device_df.copy()
display["device_category"] = display["device_category"].str.capitalize()
display = display.rename(columns={
    "device_category":           "Device",
    "product_view_sessions":     "Views",
    "checkout_sessions":         "Checkouts",
    "purchase_sessions":         "Purchases",
    "view_to_checkout_rate":     "View→Checkout %",
    "checkout_to_purchase_rate": "Checkout→Purchase %",
    "overall_purchase_rate":     "Overall %",
})
st.dataframe(
    display,
    width="stretch",
    hide_index=True,
    column_config={
        "Views": st.column_config.NumberColumn(format="%,d"),
        "Checkouts": st.column_config.NumberColumn(format="%,d"),
        "Purchases": st.column_config.NumberColumn(format="%,d"),
        "View→Checkout %": st.column_config.NumberColumn(format="%.2f"),
        "Checkout→Purchase %": st.column_config.NumberColumn(format="%.2f"),
        "Overall %": st.column_config.NumberColumn(format="%.2f"),
    },
)

st.info(
    "**Statistical note:** Mobile (6.26%) converted marginally higher than "
    "Desktop (5.91%), a difference of 0.35 percentage points. "
    "A two-proportion z-test returned p = 0.050 with a 95% CI of "
    "(−0.002%, +0.696%) — borderline significant and small in practical terms. "
    "Caution is warranted before attributing the difference to device type "
    "rather than confounding factors such as acquisition source or session intent.",
    icon="ℹ️",
)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Product opportunity table
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("Session Purchase Rate by First-Viewed Product")
st.caption(
    "Aggregated from 77,020 session-level model features. "
    "**Purchase rate** = fraction of sessions where a purchase occurred later "
    "in the same session. This does not confirm the first-viewed item was purchased."
)

# ── Filters ───────────────────────────────────────────────────────────────────
with st.expander("🔍 Filters", expanded=True):
    fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 1])

    with fc1:
        device_opts = ["All devices"] + sorted(features_df["device_category"].dropna().unique())
        device_sel  = st.selectbox("Device", device_opts)

    with fc2:
        # Clean category list
        cats = (
            features_df["first_item_category"]
            .dropna()
            .pipe(lambda s: s[~s.isin(["(unknown)", "(not set)"])])
            .unique()
        )
        cat_opts = ["All categories"] + sorted(cats)
        cat_sel  = st.selectbox("Category", cat_opts)

    with fc3:
        min_sessions = st.slider(
            "Minimum sessions", min_value=5, max_value=500, value=50, step=5,
            help="Exclude products with fewer sessions to reduce noise."
        )

    with fc4:
        include_unknown = st.checkbox(
            "Include '(unknown)' items",
            value=False,
            help="Items where the product name was not captured in GA4.",
        )

# ── Aggregate ─────────────────────────────────────────────────────────────────
agg_df = features_df.copy()

if device_sel != "All devices":
    agg_df = agg_df[agg_df["device_category"] == device_sel]

if cat_sel != "All categories":
    agg_df = agg_df[agg_df["first_item_category"] == cat_sel]

if not include_unknown:
    agg_df = agg_df[agg_df["first_item_name"] != "(unknown)"]

product_agg = (
    agg_df.groupby("first_item_name", dropna=False)
    .agg(
        product_view_sessions=("session_id", "count"),
        sessions_purchasing_later=("purchased_later_in_session", "sum"),
    )
    .reset_index()
    .rename(columns={"first_item_name": "product"})
)
product_agg["session_purchase_rate"] = (
    product_agg["sessions_purchasing_later"] / product_agg["product_view_sessions"]
)
product_agg = product_agg[product_agg["product_view_sessions"] >= min_sessions]
product_agg = product_agg.sort_values("product_view_sessions", ascending=False)

if product_agg.empty:
    st.warning(
        "No products match the current filters. "
        "Try reducing the minimum-session threshold or changing the filters."
    )
    st.stop()

# ── Summary metrics ────────────────────────────────────────────────────────────
weighted_rate = (
    product_agg["sessions_purchasing_later"].sum()
    / product_agg["product_view_sessions"].sum()
)

sm1, sm2, sm3 = st.columns(3)
sm1.metric("Products shown", f"{len(product_agg):,}")
sm2.metric("Sessions in scope", f"{product_agg['product_view_sessions'].sum():,}")
sm3.metric("Weighted session purchase rate", f"{weighted_rate*100:.2f}%")

# ── Display table ─────────────────────────────────────────────────────────────
display_agg = product_agg.copy()
display_agg["session_purchase_rate_pct"] = (
    display_agg["session_purchase_rate"] * 100
).round(2)

st.dataframe(
    display_agg[
        ["product", "product_view_sessions",
         "sessions_purchasing_later", "session_purchase_rate_pct"]
    ].rename(columns={
        "product":                    "Product",
        "product_view_sessions":      "Product-view sessions",
        "sessions_purchasing_later":  "Sessions purchasing later",
        "session_purchase_rate_pct":  "Session purchase rate %",
    }),
    width="stretch",
    hide_index=True,
    column_config={
        "Product-view sessions": st.column_config.NumberColumn(format="%,d"),
        "Sessions purchasing later": st.column_config.NumberColumn(format="%,d"),
        "Session purchase rate %": st.column_config.NumberColumn(format="%.2f"),
    },
)

st.caption(
    "**High-volume / low-propensity candidates** are products with many "
    "product-view sessions but a below-average session purchase rate. "
    "These may indicate merchandising gaps, price sensitivity, or friction "
    "in the checkout path. Controlled experiments are required before "
    "attributing low purchase rates to specific causes."
)

# ── Download ───────────────────────────────────────────────────────────────────
download_agg = display_agg[
    ["product", "product_view_sessions",
     "sessions_purchasing_later", "session_purchase_rate_pct"]
].rename(columns={
    "product":                    "product",
    "product_view_sessions":      "product_view_sessions",
    "sessions_purchasing_later":  "sessions_purchasing_later",
    "session_purchase_rate_pct":  "session_purchase_rate_pct",
})

st.download_button(
    label="⬇️ Download product table as CSV",
    data=download_agg.to_csv(index=False),
    file_name="product_purchase_propensity.csv",
    mime="text/csv",
)

st.divider()
st.info(
    "**Interpretation note:** 'Sessions purchasing later' counts sessions where "
    "a `purchase` event occurred after the first `view_item` in the same session. "
    "It does not confirm that the first-viewed product was the one purchased. "
    "All results are observational associations, not causal effects.",
    icon="ℹ️",
)
