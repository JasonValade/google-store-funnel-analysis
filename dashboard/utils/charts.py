"""
charts.py — reusable Plotly chart builders for the V4 dashboard.

All functions return a Plotly figure; none call Streamlit directly.
Color palette is Okabe-Ito (color-blind-friendly).
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

# ── Color-blind-friendly palette (Okabe-Ito) ─────────────────────────────────
C = {
    "blue":    "#0072B2",
    "orange":  "#E69F00",
    "green":   "#009E73",
    "red":     "#D55E00",
    "purple":  "#CC79A7",
    "sky":     "#56B4E9",
    "yellow":  "#F0E442",
    "gray":    "#999999",
    "black":   "#000000",
}

STATUS_COLORS = {
    "CRITICAL_TRACKING_OUTAGE": C["red"],
    "LIKELY_TRAFFIC_DECLINE":   C["orange"],
}

MODEL_COLORS = {
    "LogisticRegression": C["blue"],
    "RandomForest":       C["orange"],
    "DummyClassifier":    C["gray"],
}

CALIB_COLORS = {
    "uncalibrated":       C["orange"],
    "sigmoid_calibrated": C["blue"],
}


def _base_layout(**kwargs) -> dict:
    """Shared layout defaults applied to every chart."""
    return dict(
        font=dict(family="Inter, Arial, sans-serif", size=13),
        template="plotly",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(127,127,127,0.45)",
            borderwidth=1,
        ),
        **kwargs,
    )


def apply_theme(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply a Streamlit-compatible theme for both dark and light mode."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=15)),
        **_base_layout(),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="rgba(127,127,127,0.45)", automargin=True)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(127,127,127,0.25)", zeroline=False, automargin=True)
    return fig


# ── Funnel charts ─────────────────────────────────────────────────────────────

def funnel_chart(
    stages: list[str],
    values: list[int],
    title: str = "Purchase Funnel",
) -> go.Figure:
    """Vertical funnel chart."""
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textposition="inside",
        textinfo="value+percent initial",
        textfont=dict(size=13, color="rgba(245,245,245,0.96)"),
        marker=dict(color=[C["blue"], C["sky"], C["green"]]),
        connector=dict(line=dict(color="rgba(127,127,127,0.5)", width=1)),
    ))
    fig.update_layout(title=dict(text=title, font=dict(size=15)), **_base_layout())
    return fig


# ── Weekly conversion line chart ─────────────────────────────────────────────

def weekly_conversion_chart(
    df: pd.DataFrame,
    peak_week: str = "2020-12-07",
) -> go.Figure:
    """
    Line chart of weekly purchase conversion rate.
    df must have week_start (datetime) and purchase_conversion_rate (percentage).
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["week_start"],
        y=df["purchase_conversion_rate"],
        mode="lines+markers",
        name="Purchase conversion rate",
        line=dict(color=C["blue"], width=2.5),
        marker=dict(size=7),
        hovertemplate="%{x|%b %d}<br>Conversion: <b>%{y:.2f}%</b><extra></extra>",
    ))

    # December peak annotation
    peak_row = df[df["week_start"].astype(str).str.startswith(peak_week)]
    if not peak_row.empty:
        peak_val = float(peak_row["purchase_conversion_rate"].iloc[0])
        fig.add_annotation(
            x=peak_row["week_start"].iloc[0],
            y=peak_val,
            text=f"Peak {peak_val:.2f}%<br>(Dec 7 week)",
            showarrow=True,
            arrowhead=2,
            ax=40,
            ay=-30,
            font=dict(size=11, color=C["red"]),
            arrowcolor=C["red"],
        )

    fig.update_layout(
        xaxis_title="Week starting",
        yaxis_title="Purchase conversion rate (%)",
        yaxis_ticksuffix="%",
        hovermode="x unified",
        **_base_layout(),
    )
    apply_theme(fig, "Weekly Purchase Conversion Rate")
    return fig


# ── Device bar chart ─────────────────────────────────────────────────────────

def device_bar_chart(df: pd.DataFrame) -> go.Figure:
    """
    Grouped bar chart of overall conversion rate by device.
    df must have device_category and overall_purchase_rate (percentage).
    """
    df_sorted = df.sort_values("overall_purchase_rate", ascending=False)
    colors = [C["blue"], C["sky"], C["orange"]]

    fig = go.Figure(go.Bar(
        x=df_sorted["device_category"].str.capitalize(),
        y=df_sorted["overall_purchase_rate"],
        marker_color=colors[: len(df_sorted)],
        text=df_sorted["overall_purchase_rate"].apply(lambda v: f"{v:.2f}%"),
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Conversion rate: <b>%{y:.2f}%</b><extra></extra>",
    ))

    fig.update_layout(
        xaxis_title="Device",
        yaxis_title="Overall purchase conversion rate (%)",
        yaxis_ticksuffix="%",
        yaxis_range=[0, df_sorted["overall_purchase_rate"].max() * 1.3],
        showlegend=False,
        **_base_layout(),
    )
    apply_theme(fig, "Overall Purchase Conversion Rate by Device")
    return fig


# ── Tracking health scatter ───────────────────────────────────────────────────

def tracking_scatter(df: pd.DataFrame) -> go.Figure:
    """
    Scatter plot of tracking ratios per alert date.
    Dates are categorical on x-axis so non-consecutive dates are not connected.
    """
    x_labels = df["date"].dt.strftime("%Y-%m-%d").tolist()

    ratio_cols = [
        ("event_volume_ratio",           "Event-volume ratio",           C["red"],    "circle"),
        ("page_view_ratio",              "Page-view ratio",              C["blue"],   "square"),
        ("traffic_adjusted_event_ratio", "Traffic-adjusted event ratio", C["green"],  "diamond"),
    ]

    fig = go.Figure()
    for col, label, color, symbol in ratio_cols:
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=df[col],
            mode="markers",
            name=label,
            marker=dict(color=color, symbol=symbol, size=12, line=dict(width=1.5, color="rgba(127,127,127,0.6)")),
            customdata=df[["event_label", "status_label", "event_name", "tracking_status"]].values,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Event: %{customdata[0]}<br>"
                f"{label}: <b>%{{y:.3f}}</b><br>"
                "Status: %{customdata[1]}<br>"
                "<span style='opacity:0.75'>Raw event: %{customdata[2]} · Raw status: %{customdata[3]}</span>"
                "<extra></extra>"
            ),
        ))

    # Reference line at 1.0
    fig.add_hline(
        y=1.0,
        line_dash="dash",
        line_color=C["gray"],
        annotation_text="Baseline = 1.0",
    )

    fig.update_layout(
        xaxis_title="Alert date",
        yaxis_title="Ratio (1.0 = expected)",
        yaxis_range=[-0.05, 1.4],
        xaxis_type="category",
        hovermode="x unified",
        **_base_layout(),
    )
    apply_theme(fig, "Tracking Health — Alert Ratios")
    return fig


# ── PR curves ────────────────────────────────────────────────────────────────

def pr_curves_chart(df: pd.DataFrame, no_skill: float) -> go.Figure:
    """
    Precision-recall curves for LR and RF (validation set).
    df must have model, recall, precision columns.
    """
    fig = go.Figure()

    # No-skill baseline
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[no_skill, no_skill],
        mode="lines",
        name=f"No-skill baseline (PR-AUC = {no_skill:.3f})",
        line=dict(color=C["gray"], dash="dash", width=1.5),
        hoverinfo="skip",
    ))

    for model_name, color in MODEL_COLORS.items():
        sub = df[df["model"] == model_name].sort_values("recall")
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["recall"],
            y=sub["precision"],
            mode="lines",
            name=model_name,
            line=dict(color=color, width=2.5),
            hovertemplate="Recall: %{x:.3f}<br>Precision: %{y:.3f}<extra></extra>",
        ))

    fig.update_layout(
        xaxis_title="Recall",
        yaxis_title="Precision",
        xaxis_range=[0, 1],
        yaxis_range=[0, 1],
        hovermode="x unified",
        **_base_layout(),
    )
    apply_theme(fig, "Precision-Recall Curves — Validation Set")
    return fig


# ── Calibration curves ────────────────────────────────────────────────────────

def calibration_chart(df: pd.DataFrame) -> go.Figure:
    """
    Calibration curves (uncalibrated and sigmoid calibrated) on the test set.
    """
    fig = go.Figure()

    # Perfect calibration reference
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1],
        mode="lines",
        name="Perfect calibration",
        line=dict(color=C["gray"], dash="dash", width=1.5),
        hoverinfo="skip",
    ))

    label_map = {
        "uncalibrated":       "Uncalibrated",
        "sigmoid_calibrated": "Sigmoid calibrated",
    }
    symbol_map = {"uncalibrated": "square", "sigmoid_calibrated": "circle"}

    for cal_type, color in CALIB_COLORS.items():
        sub = df[df["calibration_type"] == cal_type]
        fig.add_trace(go.Scatter(
            x=sub["mean_predicted_probability"],
            y=sub["observed_positive_fraction"],
            mode="lines+markers",
            name=label_map.get(cal_type, cal_type),
            line=dict(color=color, width=2.5),
            marker=dict(symbol=symbol_map.get(cal_type, "circle"), size=8),
            hovertemplate="Predicted: %{x:.4f}<br>Observed: %{y:.4f}<extra></extra>",
        ))

    fig.update_layout(
        xaxis_title="Mean predicted probability",
        yaxis_title="Observed positive fraction",
        xaxis_range=[0, None],
        yaxis_range=[0, None],
        **_base_layout(),
    )
    apply_theme(fig, "Probability Calibration Curves — Test Set")
    return fig


# ── Decile lift bar chart ─────────────────────────────────────────────────────

def decile_chart(df: pd.DataFrame) -> go.Figure:
    """
    Purchase rate by risk decile bar chart (test set).
    df has risk_decile (1=highest), purchase_rate (proportion), overall_test_purchase_rate.
    """
    overall_pct = float(df["overall_test_purchase_rate"].iloc[0]) * 100
    pct = (df["purchase_rate"] * 100).round(2)

    fig = go.Figure(go.Bar(
        x=df["risk_decile"],
        y=pct,
        marker_color=C["blue"],
        text=pct.apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
        customdata=df[["session_count", "purchase_count", "lift"]].values,
        hovertemplate=(
            "Decile %{x}<br>"
            "Purchase rate: <b>%{y:.2f}%</b><br>"
            "Sessions: %{customdata[0]:,}<br>"
            "Purchases: %{customdata[1]:,}<br>"
            "Lift: <b>%{customdata[2]:.2f}x</b><extra></extra>"
        ),
    ))

    fig.add_hline(
        y=overall_pct,
        line_dash="dash",
        line_color=C["red"],
        annotation_text=f"Overall test rate {overall_pct:.2f}%",
        annotation_position="top right",
    )

    fig.update_layout(
        xaxis_title="Risk decile (1 = highest predicted risk)",
        yaxis_title="Purchase rate (%)",
        yaxis_ticksuffix="%",
        yaxis_range=[0, pct.max() * 1.3],
        xaxis_dtick=1,
        showlegend=False,
        **_base_layout(),
    )
    apply_theme(fig, "Purchase Rate by Predicted-Risk Decile — Calibrated RF, Test Set")
    return fig


# ── Logistic coefficient chart ────────────────────────────────────────────────

def coefficient_chart(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart of top-20 LR coefficients by absolute magnitude.
    Colored by direction; sorted by coefficient value.
    """
    df_sorted = df.sort_values("coefficient")
    colors = [
        C["blue"] if c > 0 else C["red"]
        for c in df_sorted["coefficient"]
    ]
    def _feature_label(raw: str) -> str:
        scope, value = raw.split("__", 1) if "__" in raw else ("", raw)
        if value.startswith("first_item_name_"):
            return f"First item name: {value.replace('first_item_name_', '', 1)}"
        if value.startswith("first_item_category_"):
            return f"First item category: {value.replace('first_item_category_', '', 1)}"
        if value.startswith("country_"):
            return f"Country: {value.replace('country_', '', 1)}"
        if value.startswith("device_category_"):
            return f"Device: {value.replace('device_category_', '', 1)}"
        if value.startswith("acquisition_source_"):
            return f"Acquisition source: {value.replace('acquisition_source_', '', 1)}"
        if value.startswith("acquisition_medium_"):
            return f"Acquisition medium: {value.replace('acquisition_medium_', '', 1)}"

        replacements = {
            "seconds_log1p": "Seconds to first view (log1p)",
            "page_views_before_first_view_log1p": "Page views before first view (log1p)",
            "scroll_events_before_first_view_log1p": "Scroll events before first view (log1p)",
            "search_events_before_first_view_log1p": "Search events before first view (log1p)",
            "promotion_views_before_first_view_log1p": "Promotion views before first view (log1p)",
            "engagement_events_before_first_view_log1p": "Engagement events before first view (log1p)",
            "hour_sin": "Hour of day (sin)",
            "hour_cos": "Hour of day (cos)",
            "dow_sin": "Day of week (sin)",
            "dow_cos": "Day of week (cos)",
            "item_metadata_missing": "Item metadata missing flag",
            "long_pre_view_session": "Long pre-view session flag",
            "is_new_visitor": "New visitor flag",
            "first_item_price": "First item price (log1p)",
        }
        return replacements.get(value, value.replace("_", " ").title())

    labels = df_sorted["feature"].map(_feature_label)

    fig = go.Figure(go.Bar(
        x=df_sorted["coefficient"],
        y=labels,
        orientation="h",
        marker_color=colors,
        customdata=df_sorted[["feature", "absolute_coefficient", "direction"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Coefficient: %{x:.4f}<br>"
            "|Coefficient|: %{customdata[1]:.4f}<br>"
            "Raw feature: %{customdata[0]}<br>"
            "%{customdata[2]}<extra></extra>"
        ),
    ))

    fig.add_vline(x=0, line_color=C["gray"], line_width=1)

    fig.update_layout(
        xaxis_title="Logistic regression coefficient (association only — not causal)",
        yaxis_title="",
        height=680,
        margin=dict(l=20, r=10, t=50, b=10),
        showlegend=False,
        **{k: v for k, v in _base_layout().items() if k not in ("margin",)},
    )
    apply_theme(fig, "Top-20 Logistic Regression Feature Associations")
    return fig
