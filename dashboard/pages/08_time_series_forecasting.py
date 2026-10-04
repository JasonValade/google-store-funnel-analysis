"""
08_time_series_forecasting.py — Time-Series Forecasting page.
"""

import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats

from dashboard.utils.data_loader import (
    load_weekly_conversion,
    render_sidebar,
)

render_sidebar()

st.markdown(
    """
    <div class="page-hero">
      <div class="eyebrow">📈 Predictive analytics</div>
      <div class="headline">Time-Series Forecasting</div>
      <div class="subhead">
        Forecast future conversion rates and purchase volumes for proactive planning
        and resource allocation. Identify seasonal patterns and trends for business optimization.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.title("📈 Time-Series Forecasting")
st.caption(
    "Predictive analytics for conversion rates and purchase volumes · "
    "Seasonal pattern analysis and trend forecasting"
)
st.info(
    "Use this tool to forecast future performance, identify seasonal patterns, and plan resources accordingly.",
    icon="🔮",
)

# Load data
weekly_df = load_weekly_conversion()
weekly_df_clean = weekly_df[weekly_df['week_start'] > '2020-10-31'].copy()

# Convert conversion rates from percentage to decimal
weekly_df_clean['view_to_checkout_rate'] = weekly_df_clean['view_to_checkout_rate'] / 100
weekly_df_clean['checkout_to_purchase_rate'] = weekly_df_clean['checkout_to_purchase_rate'] / 100
weekly_df_clean['purchase_conversion_rate'] = weekly_df_clean['purchase_conversion_rate'] / 100

st.divider()

# Historical overview
st.subheader("📊 Historical Overview")

col_hist1, col_hist2, col_hist3 = st.columns(3)

with col_hist1:
    st.metric(
        "Analysis Period",
        f"{len(weekly_df_clean)} weeks",
        help="Number of weeks in historical data"
    )

with col_hist2:
    avg_conversion = weekly_df_clean['purchase_conversion_rate'].mean()
    st.metric(
        "Avg Conversion Rate",
        f"{avg_conversion:.2%}",
        help="Average historical conversion rate"
    )

with col_hist3:
    avg_purchases = weekly_df_clean['purchase_sessions'].mean()
    st.metric(
        "Avg Weekly Purchases",
        f"{avg_purchases:,.0f}",
        help="Average weekly purchase volume"
    )

st.divider()

# Trend analysis
st.subheader("📉 Trend Analysis")

# Calculate linear trend
x = np.arange(len(weekly_df_clean))
y = weekly_df_clean['purchase_conversion_rate'].values
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

col_trend1, col_trend2 = st.columns(2)

with col_trend1:
    trend_direction = "Increasing" if slope > 0 else "Decreasing"
    st.metric(
        "Trend Direction",
        trend_direction,
        delta=f"{slope * 100:.4f}%/week",
        help="Linear trend direction and slope"
    )

with col_trend2:
    st.metric(
        "Trend Strength (R²)",
        f"{r_value**2:.4f}",
        help="How well the linear trend fits the data (0-1)"
    )

# Plot historical trend
st.line_chart(
    weekly_df_clean.set_index('week_start')['purchase_conversion_rate']
)

st.caption(
    f"**Trend Analysis**: {trend_direction} trend with R² = {r_value**2:.4f}. "
    f"P-value: {p_value:.4f} {'(statistically significant)' if p_value < 0.05 else '(not statistically significant)'}"
)

st.divider()

# Seasonal pattern analysis
st.subheader("🗓️ Seasonal Pattern Analysis")

# Extract month
weekly_df_clean['month'] = weekly_df_clean['week_start'].dt.month
monthly_avg = weekly_df_clean.groupby('month')['purchase_conversion_rate'].mean()

month_names = ['November', 'December', 'January']
col_season1, col_season2 = st.columns(2)

with col_season1:
    peak_month = month_names[monthly_avg.argmax()]
    st.metric(
        "Peak Month",
        peak_month,
        delta=f"{monthly_avg.max():.2%}",
        help="Month with highest average conversion rate"
    )

with col_season2:
    low_month = month_names[monthly_avg.argmin()]
    st.metric(
        "Lowest Month",
        low_month,
        delta=f"{monthly_avg.min():.2%}",
        help="Month with lowest average conversion rate"
    )

# Plot seasonal pattern
seasonal_df = pd.DataFrame({
    'Month': month_names,
    'Avg Conversion Rate': monthly_avg.values
})

st.bar_chart(
    seasonal_df.set_index('Month')
)

st.caption(
    f"**Seasonal Variation**: {monthly_avg.max() - monthly_avg.min():.2%} difference between peak and low months. "
    "Note: Limited data (3 months) - patterns may not represent typical seasonal behavior."
)

st.divider()

# Forecast configuration
st.subheader("🔮 Forecast Configuration")

col_forecast1, col_forecast2 = st.columns(2)

with col_forecast1:
    forecast_periods = st.number_input(
        "Forecast Horizon (weeks)",
        min_value=1,
        max_value=12,
        value=8,
        step=1,
        help="Number of weeks to forecast ahead"
    )

with col_forecast2:
    confidence_level = st.selectbox(
        "Confidence Level",
        [0.80, 0.90, 0.95, 0.99],
        index=2,
        help="Confidence level for prediction intervals"
    )

# Forecast model selection
forecast_model = st.selectbox(
    "Forecast Model",
    ["Linear Trend", "Simple Moving Average", "Exponential Smoothing"],
    index=0,
    help="Choose forecasting method"
)

st.divider()

# Generate forecasts
st.subheader("📊 Forecast Results")

def linear_trend_forecast(series, periods):
    """Linear trend forecast using OLS regression."""
    x = np.arange(len(series))
    y = series.values
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    forecasts = []
    for i in range(periods):
        forecast = intercept + slope * (len(series) + i)
        forecasts.append(forecast)

    return forecasts, {'slope': slope, 'intercept': intercept, 'r_squared': r_value**2}

def simple_moving_average_forecast(series, window=4, periods=8):
    """Simple moving average forecast."""
    forecasts = []
    series_copy = series.copy()
    for _i in range(periods):
        forecast = series_copy.tail(window).mean()
        forecasts.append(forecast)
        series_copy = pd.concat([series_copy, pd.Series([forecast])])
    return forecasts

def exponential_smoothing_forecast(series, alpha=0.3, periods=8):
    """Simple exponential smoothing forecast."""
    smoothed = [series.iloc[0]]
    for i in range(1, len(series)):
        smoothed.append(alpha * series.iloc[i] + (1 - alpha) * smoothed[-1])

    forecasts = []
    last_smoothed = smoothed[-1]
    for _i in range(periods):
        forecasts.append(last_smoothed)
    return forecasts

# Generate forecasts based on selected model
if forecast_model == "Linear Trend":
    conversion_forecast, model_params = linear_trend_forecast(
        weekly_df_clean['purchase_conversion_rate'],
        forecast_periods
    )
    purchase_forecast, _ = linear_trend_forecast(
        weekly_df_clean['purchase_sessions'],
        forecast_periods
    )
elif forecast_model == "Simple Moving Average":
    conversion_forecast = simple_moving_average_forecast(
        weekly_df_clean['purchase_conversion_rate'],
        window=4,
        periods=forecast_periods
    )
    purchase_forecast = simple_moving_average_forecast(
        weekly_df_clean['purchase_sessions'],
        window=4,
        periods=forecast_periods
    )
else:  # Exponential Smoothing
    conversion_forecast = exponential_smoothing_forecast(
        weekly_df_clean['purchase_conversion_rate'],
        alpha=0.3,
        periods=forecast_periods
    )
    purchase_forecast = exponential_smoothing_forecast(
        weekly_df_clean['purchase_sessions'],
        alpha=0.3,
        periods=forecast_periods
    )

# Calculate confidence intervals
def calculate_ci(historical_data, forecast, confidence_level):
    """Calculate confidence intervals based on historical volatility."""
    std_dev = historical_data.std()
    z_score = stats.norm.ppf((1 + confidence_level) / 2)

    ci_lower = []
    ci_upper = []
    for i, f in enumerate(forecast):
        uncertainty = std_dev * np.sqrt(1 + i / len(historical_data))
        ci_lower.append(f - z_score * uncertainty)
        ci_upper.append(f + z_score * uncertainty)

    return ci_lower, ci_upper

conv_ci_lower, conv_ci_upper = calculate_ci(
    weekly_df_clean['purchase_conversion_rate'],
    conversion_forecast,
    confidence_level
)

pur_ci_lower, pur_ci_upper = calculate_ci(
    weekly_df_clean['purchase_sessions'],
    purchase_forecast,
    confidence_level
)

# Create forecast dates
last_date = weekly_df_clean['week_start'].iloc[-1]
future_dates = pd.date_range(
    start=last_date + pd.Timedelta(weeks=1),
    periods=forecast_periods,
    freq='W-MON'
)

# Create forecast dataframe
forecast_df = pd.DataFrame({
    'week_start': future_dates,
    'conversion_rate_forecast': conversion_forecast,
    'conversion_rate_lower': conv_ci_lower,
    'conversion_rate_upper': conv_ci_upper,
    'purchase_volume_forecast': purchase_forecast,
    'purchase_volume_lower': pur_ci_lower,
    'purchase_volume_upper': pur_ci_upper
})

# Display forecast table
st.dataframe(
    forecast_df[['week_start', 'conversion_rate_forecast', 'conversion_rate_lower', 'conversion_rate_upper']],
    hide_index=True
)

st.divider()

# Visualization
st.subheader("📈 Forecast Visualization")

# Combine historical and forecast for plotting
historical_conv = weekly_df_clean[['week_start', 'purchase_conversion_rate']].copy()
historical_conv['type'] = 'Historical'

forecast_conv = forecast_df[['week_start', 'conversion_rate_forecast']].copy()
forecast_conv.columns = ['week_start', 'purchase_conversion_rate']
forecast_conv['type'] = 'Forecast'

combined_conv = pd.concat([historical_conv, forecast_conv])

# Plot conversion rate forecast
st.line_chart(
    combined_conv.set_index('week_start')['purchase_conversion_rate']
)

st.caption(
    f"**{forecast_model} Forecast**: {forecast_periods} weeks ahead with {confidence_level*100:.0f}% confidence interval. "
    "Forecast uncertainty increases over time."
)

st.divider()

# Purchase volume forecast
st.subheader("📦 Purchase Volume Forecast")

st.dataframe(
    forecast_df[['week_start', 'purchase_volume_forecast', 'purchase_volume_lower', 'purchase_volume_upper']],
    hide_index=True
)

# Plot purchase volume forecast
historical_pur = weekly_df_clean[['week_start', 'purchase_sessions']].copy()
historical_pur['type'] = 'Historical'

forecast_pur = forecast_df[['week_start', 'purchase_volume_forecast']].copy()
forecast_pur.columns = ['week_start', 'purchase_sessions']
forecast_pur['type'] = 'Forecast'

combined_pur = pd.concat([historical_pur, forecast_pur])

st.line_chart(
    combined_pur.set_index('week_start')['purchase_sessions']
)

st.divider()

# Business impact
st.subheader("💼 Business Impact")

# Calculate business metrics
avg_weekly_purchases = weekly_df_clean['purchase_sessions'].mean()
forecast_weekly_purchases = np.mean(purchase_forecast)
forecast_change_pct = ((forecast_weekly_purchases - avg_weekly_purchases) / avg_weekly_purchases) * 100

aov = st.number_input(
    "Average Order Value ($) for revenue calculation",
    min_value=10,
    max_value=500,
    value=75,
    step=5,
    help="Estimated average order value"
)

current_weekly_revenue = avg_weekly_purchases * aov
forecast_weekly_revenue = forecast_weekly_purchases * aov
revenue_change = forecast_weekly_revenue - current_weekly_revenue

col_impact1, col_impact2, col_impact3 = st.columns(3)

with col_impact1:
    st.metric(
        "Forecast Change",
        f"{forecast_change_pct:+.1f}%",
        delta=f"{forecast_change_pct:+.1f}%",
        help="Percentage change in weekly purchases"
    )

with col_impact2:
    st.metric(
        "Weekly Revenue Change",
        f"${revenue_change:+,.0f}",
        help=f"Change in weekly revenue at ${aov} AOV"
    )

with col_impact3:
    st.metric(
        "Annual Revenue Change",
        f"${revenue_change * 52:+,.0f}",
        help="Annualized revenue change"
    )

st.divider()

# Risk assessment
st.subheader("⚠️ Risk Assessment")

forecast_volatility = np.std(purchase_forecast)
revenue_volatility = forecast_volatility * aov

col_risk1, col_risk2 = st.columns(2)

with col_risk1:
    st.metric(
        "Forecast Volatility",
        f"{forecast_volatility:.0f} purchases/week",
        help="Standard deviation of forecasted purchases"
    )

with col_risk2:
    st.metric(
        "Revenue Volatility",
        f"${revenue_volatility:,.0f}/week",
        help="Standard deviation of forecasted revenue"
    )

st.divider()

# Recommendations
st.subheader("🎯 Recommendations")

recommendations = []

if forecast_change_pct > 5:
    recommendations.append("📈 **Increasing Trend**: Plan for increased inventory and staffing to meet higher demand.")
    recommendations.append("📦 **Inventory**: Increase inventory orders based on upward trend forecast.")
elif forecast_change_pct < -5:
    recommendations.append("📉 **Decreasing Trend**: Investigate causes of decline and plan recovery campaigns.")
    recommendations.append("📦 **Inventory**: Reduce inventory orders to match declining demand.")
else:
    recommendations.append("➡️ **Stable Trend**: Maintain current inventory levels and continue monitoring.")

recommendations.append("🎯 **Risk Management**: Use confidence intervals for contingency planning and buffer inventory.")
recommendations.append("📊 **Monitoring**: Re-forecast monthly with updated data to adjust plans as conditions change.")
recommendations.append("🧪 **Validation**: Compare forecasts to actuals regularly to improve model accuracy.")

for rec in recommendations:
    st.markdown(rec)

st.divider()

st.warning(
    "**Forecast Limitations**: Based on limited historical data (3 months, holiday season). "
    "Forecasts assume historical patterns continue and do not account for external factors "
    "(promotions, events, economic changes). Use as planning guidance, not absolute predictions.",
    icon="⚠️"
)
