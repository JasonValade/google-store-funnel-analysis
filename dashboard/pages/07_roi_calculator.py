"""
07_roi_calculator.py — ROI & What-If Calculator page.
"""

import pandas as pd
import streamlit as st

from dashboard.utils.data_loader import (
    load_device_funnel,
    load_weekly_conversion,
    render_sidebar,
)

render_sidebar()

st.markdown(
    """
    <div class="page-hero">
      <div class="eyebrow">💰 Business planning</div>
      <div class="headline">ROI & What-If Calculator</div>
      <div class="subhead">
        Model conversion improvements and estimate revenue impact with confidence intervals.
        Use this tool to prioritize optimization initiatives and justify investment decisions.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.title("💰 ROI & What-If Calculator")
st.caption(
    "Interactive scenario planning for conversion optimization · "
    "Estimate revenue impact and ROI for improvement initiatives"
)
st.info(
    "Adjust the sliders below to model different improvement scenarios and see the projected business impact.",
    icon="💡",
)

# Load data
device_df = load_device_funnel()
weekly_df = load_weekly_conversion()

# Calculate baseline metrics
weekly_df_clean = weekly_df[weekly_df["week_start"] > "2020-10-31"].copy()

baseline_views = weekly_df_clean["product_view_sessions"].mean()
baseline_view_to_checkout = weekly_df_clean["view_to_checkout_rate"].mean() / 100
baseline_checkout_to_purchase = weekly_df_clean["checkout_to_purchase_rate"].mean() / 100
baseline_purchases = weekly_df_clean["purchase_sessions"].mean()
baseline_conversion = baseline_view_to_checkout * baseline_checkout_to_purchase

st.divider()

# Configuration section
st.subheader("📊 Baseline Configuration")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Avg Weekly Product Views",
        f"{baseline_views:,.0f}",
        help="Average weekly product view sessions (historical)",
    )

with col2:
    st.metric(
        "Avg Weekly Purchases",
        f"{baseline_purchases:,.0f}",
        help="Average weekly purchase sessions (historical)",
    )

with col3:
    st.metric(
        "Overall Conversion Rate",
        f"{baseline_conversion:.2%}",
        help="Current overall conversion rate (view → purchase)",
    )

st.divider()

# AOV configuration
st.subheader("💵 Average Order Value (AOV)")

col_aov1, col_aov2 = st.columns([1, 2])

with col_aov1:
    aov = st.number_input(
        "Average Order Value ($)",
        min_value=10,
        max_value=500,
        value=75,
        step=5,
        help="Estimated average order value for revenue calculations",
    )

with col_aov2:
    st.info(
        f"**Current weekly revenue estimate:** ${baseline_purchases * aov:,.0f}  \n"
        f"**Current annual revenue estimate:** ${baseline_purchases * aov * 52:,.0f}",
        icon="📈",
    )

st.divider()

# Improvement scenario configuration
st.subheader("🎯 Improvement Scenario Configuration")

col_vc, col_cp = st.columns(2)

with col_vc:
    view_checkout_improvement = st.slider(
        "View-to-Checkout Improvement (%)",
        min_value=0,
        max_value=100,
        value=20,
        step=5,
        help="Percentage improvement in view-to-checkout conversion rate",
    )

with col_cp:
    checkout_purchase_improvement = st.slider(
        "Checkout-to-Purchase Improvement (%)",
        min_value=0,
        max_value=100,
        value=20,
        step=5,
        help="Percentage improvement in checkout-to-purchase conversion rate",
    )

# Calculate projected metrics
improved_view_to_checkout = baseline_view_to_checkout * (1 + view_checkout_improvement / 100)
improved_checkout_to_purchase = baseline_checkout_to_purchase * (
    1 + checkout_purchase_improvement / 100
)
improved_conversion = improved_view_to_checkout * improved_checkout_to_purchase

new_checkouts = baseline_views * improved_view_to_checkout
new_purchases = new_checkouts * improved_checkout_to_purchase
baseline_purchases_current = (
    baseline_views * baseline_view_to_checkout * baseline_checkout_to_purchase
)

additional_purchases_weekly = new_purchases - baseline_purchases_current
additional_purchases_annually = additional_purchases_weekly * 52

current_weekly_revenue = baseline_purchases_current * aov
new_weekly_revenue = new_purchases * aov
weekly_revenue_lift = new_weekly_revenue - current_weekly_revenue
annual_revenue_lift = weekly_revenue_lift * 52

lift_percentage = (weekly_revenue_lift / current_weekly_revenue) * 100

st.divider()

# Results section
st.subheader("📈 Projected Impact")

col_impact1, col_impact2, col_impact3 = st.columns(3)

with col_impact1:
    st.metric(
        "New Overall Conversion Rate",
        f"{improved_conversion:.2%}",
        delta=f"{improved_conversion - baseline_conversion:+.2%}",
        help="Projected overall conversion rate after improvements",
    )

with col_impact2:
    st.metric(
        "Additional Weekly Purchases",
        f"{additional_purchases_weekly:,.0f}",
        delta=f"{additional_purchases_weekly:,.0f}",
        help="Additional purchases per week from improvements",
    )

with col_impact3:
    st.metric(
        "Weekly Revenue Lift",
        f"${weekly_revenue_lift:,.0f}",
        delta=f"+{lift_percentage:.1f}%",
        help="Additional weekly revenue from improvements",
    )

st.divider()

# Annual projection
st.subheader("📅 Annual Projection")

col_annual1, col_annual2 = st.columns(2)

with col_annual1:
    st.metric(
        "Annual Revenue Lift",
        f"${annual_revenue_lift:,.0f}",
        help="Projected annual revenue increase from improvements",
    )

with col_annual2:
    st.metric(
        "Additional Annual Purchases",
        f"{additional_purchases_annually:,.0f}",
        help="Projected additional purchases per year",
    )

st.divider()

# ROI Calculator
st.subheader("💼 ROI Analysis")

st.caption("Calculate ROI with implementation costs")

col_cost1, col_cost2, col_cost3 = st.columns(3)

with col_cost1:
    implementation_cost = st.number_input(
        "One-time Implementation Cost ($)",
        min_value=0,
        max_value=100000,
        value=10000,
        step=1000,
        help="One-time cost to implement the improvements",
    )

with col_cost2:
    ongoing_monthly_cost = st.number_input(
        "Ongoing Monthly Cost ($)",
        min_value=0,
        max_value=10000,
        value=200,
        step=50,
        help="Monthly operational costs (e.g., licensing, maintenance)",
    )

with col_cost3:
    time_horizon_months = st.number_input(
        "Time Horizon (months)",
        min_value=1,
        max_value=60,
        value=12,
        step=1,
        help="Time horizon for ROI calculation",
    )

# Calculate ROI
total_ongoing_cost = ongoing_monthly_cost * time_horizon_months
total_cost = implementation_cost + total_ongoing_cost
total_benefit = annual_revenue_lift * (time_horizon_months / 12)
net_benefit = total_benefit - total_cost
roi = ((total_benefit - total_cost) / total_cost) * 100 if total_cost > 0 else 0

monthly_benefit = annual_revenue_lift / 12
payback_months = implementation_cost / monthly_benefit if monthly_benefit > 0 else float("inf")

st.divider()

# ROI Results
col_roi1, col_roi2, col_roi3 = st.columns(3)

with col_roi1:
    roi_color = "normal" if roi > 0 else "inverse"
    st.metric(
        "ROI",
        f"{roi:.0f}%",
        delta=f"{roi:.0f}%",
        help="Return on investment as percentage of total cost",
    )

with col_roi2:
    st.metric(
        "Net Benefit",
        f"${net_benefit:,.0f}",
        help="Total benefit minus total costs over time horizon",
    )

with col_roi3:
    payback_display = f"{payback_months:.1f} months" if payback_months != float("inf") else "Never"
    st.metric(
        "Payback Period", payback_display, help="Time to recover one-time implementation cost"
    )

st.divider()

# Cost breakdown
st.subheader("💸 Cost Breakdown")

col_cost_breakdown1, col_cost_breakdown2 = st.columns(2)

with col_cost_breakdown1:
    st.metric(
        "Total Implementation Cost",
        f"${implementation_cost:,.0f}",
        help="One-time implementation cost",
    )

with col_cost_breakdown2:
    st.metric(
        "Total Ongoing Cost",
        f"${total_ongoing_cost:,.0f}",
        help=f"${ongoing_monthly_cost:,.0f}/month × {time_horizon_months} months",
    )

st.metric("Total Cost", f"${total_cost:,.0f}", help="Sum of implementation and ongoing costs")

st.divider()

# Scenario comparison
st.subheader("🔄 Scenario Comparison")

st.caption("Compare different improvement scenarios side-by-side")

# Create comparison scenarios
comparison_scenarios = [
    {
        "name": "Conservative",
        "view_checkout": 10,
        "checkout_purchase": 10,
        "cost": 5000,
        "monthly": 100,
    },
    {
        "name": "Moderate",
        "view_checkout": 20,
        "checkout_purchase": 20,
        "cost": 10000,
        "monthly": 200,
    },
    {
        "name": "Aggressive",
        "view_checkout": 30,
        "checkout_purchase": 30,
        "cost": 20000,
        "monthly": 300,
    },
]

comparison_data = []
for scenario in comparison_scenarios:
    vc_imp = scenario["view_checkout"]
    cp_imp = scenario["checkout_purchase"]

    imp_vc = baseline_view_to_checkout * (1 + vc_imp / 100)
    imp_cp = baseline_checkout_to_purchase * (1 + cp_imp / 100)
    imp_conv = imp_vc * imp_cp

    new_chk = baseline_views * imp_vc
    new_pur = new_chk * imp_cp
    base_pur = baseline_views * baseline_view_to_checkout * baseline_checkout_to_purchase

    add_pur_weekly = new_pur - base_pur
    add_pur_annual = add_pur_weekly * 52

    week_rev_lift = add_pur_weekly * aov
    ann_rev_lift = week_rev_lift * 52

    total_cost = scenario["cost"] + scenario["monthly"] * time_horizon_months
    total_benefit = ann_rev_lift * (time_horizon_months / 12)
    net_benefit = total_benefit - total_cost
    roi_calc = ((total_benefit - total_cost) / total_cost) * 100 if total_cost > 0 else 0

    comparison_data.append(
        {
            "Scenario": scenario["name"],
            "V-C Improvement (%)": vc_imp,
            "C-P Improvement (%)": cp_imp,
            "New Conversion (%)": f"{imp_conv:.2%}",
            "Annual Revenue Lift ($)": f"${ann_rev_lift:,.0f}",
            "Total Cost ($)": f"${total_cost:,.0f}",
            "Net Benefit ($)": f"${net_benefit:,.0f}",
            "ROI (%)": f"{roi_calc:.0f}%",
        }
    )

comparison_df = pd.DataFrame(comparison_data)
st.dataframe(comparison_df, hide_index=True)

st.divider()

# Key insights
st.subheader("🎯 Key Insights")

insights = []

if lift_percentage > 20:
    insights.append(
        "✅ **High Impact**: This scenario would significantly improve conversion rates and revenue."
    )
elif lift_percentage > 10:
    insights.append("✅ **Moderate Impact**: This scenario would provide meaningful improvement.")
else:
    insights.append(
        "⚠️ **Low Impact**: Consider more aggressive improvements or focus on higher-impact areas."
    )

if roi > 100:
    insights.append("✅ **Excellent ROI**: Returns exceed investment by more than 100%.")
elif roi > 50:
    insights.append("✅ **Good ROI**: Returns exceed investment by more than 50%.")
elif roi > 0:
    insights.append("✅ **Positive ROI**: Returns exceed investment, but consider alternatives.")
else:
    insights.append("❌ **Negative ROI**: Costs exceed benefits. Reconsider this approach.")

if payback_months < 6:
    insights.append("✅ **Quick Payback**: Investment recovered in less than 6 months.")
elif payback_months < 12:
    insights.append("✅ **Reasonable Payback**: Investment recovered within a year.")
elif payback_months < 24:
    insights.append("⚠️ **Long Payback**: Investment takes 1-2 years to recover.")
else:
    insights.append("❌ **Very Long Payback**: Investment takes more than 2 years to recover.")

for insight in insights:
    st.markdown(insight)

st.divider()

st.info(
    "**Note**: These projections are based on historical data and assumptions. "
    "Actual results may vary. Validate assumptions through A/B testing before making significant investments.",
    icon="⚠️",
)
