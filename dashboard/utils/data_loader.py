"""
data_loader.py — cached artifact loaders for the V4 dashboard.

Resolves the repository root from this file's location so the app works
regardless of the working directory when Streamlit is launched.
Never queries BigQuery or requires Google credentials.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

# Resolve repository root: dashboard/utils/data_loader.py → repo/
_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent.parent
_DEMO = _REPO / "data" / "processed" / "demo"


def _demo_path(filename: str) -> Path:
    p = _DEMO / filename
    if not p.exists():
        st.error(
            f"Missing artifact: `{p.relative_to(_REPO)}`  \n"
            "Re-run `notebooks/03_purchase_prediction.ipynb` to regenerate "
            "dashboard artifacts."
        )
        st.stop()
    return p


# ── Small CSV loaders ────────────────────────────────────────────────────────

@st.cache_data
def load_device_funnel() -> pd.DataFrame:
    """3-row device breakdown. Rate columns stored as percentages (e.g. 6.26)."""
    return pd.read_csv(_demo_path("device_funnel.csv"))


@st.cache_data
def load_weekly_conversion() -> pd.DataFrame:
    """14-row weekly funnel. Rate columns stored as percentages. week_start is date."""
    df = pd.read_csv(_demo_path("weekly_conversion.csv"), parse_dates=["week_start"])
    return df


@st.cache_data
def load_tracking_alerts() -> pd.DataFrame:
    """6-row alert log. Ratio columns are proportions (0–1). date is string yyyy-mm-dd."""
    df = pd.read_csv(_demo_path("tracking_alerts.csv"), parse_dates=["date"])
    return df


# ── Model artifact loaders ────────────────────────────────────────────────────

@st.cache_data
def load_model_metrics() -> dict:
    """36-key JSON. Rates stored as proportions (0–1), e.g. test_pr_auc=0.140."""
    with open(_demo_path("model_metrics.json")) as fh:
        return json.load(fh)


@st.cache_data
def load_validation_comparison() -> pd.DataFrame:
    """3-row validation table (Dummy, LR, RF). Rates are proportions."""
    return pd.read_csv(_demo_path("model_validation_comparison.csv"))


@st.cache_data
def load_pr_curves() -> pd.DataFrame:
    """18 k-row long-format precision-recall curves (validation set)."""
    return pd.read_csv(_demo_path("model_pr_curves.csv"))


@st.cache_data
def load_calibration_curves() -> pd.DataFrame:
    """20-row calibration data (uncalibrated + sigmoid_calibrated, test set)."""
    return pd.read_csv(_demo_path("model_calibration_curves.csv"))


@st.cache_data
def load_test_deciles() -> pd.DataFrame:
    """10-row decile table (calibrated RF, test set). Rates are proportions."""
    return pd.read_csv(_demo_path("model_test_deciles.csv"))


@st.cache_data
def load_logistic_coefficients() -> pd.DataFrame:
    """20-row top-LR coefficient table. Associations, NOT causal effects."""
    return pd.read_csv(_demo_path("model_logistic_coefficients.csv"))


# ── Large feature file ────────────────────────────────────────────────────────

@st.cache_data
def load_model_features() -> pd.DataFrame:
    """
    77 020-row session-level feature file (gzip-compressed).
    session_id is intentionally excluded from display.
    Rates stored as integer 0/1 in purchased_later_in_session.
    """
    df = pd.read_csv(
        _demo_path("model_features.csv.gz"),
        parse_dates=["session_date"],
        compression="gzip",
    )
    return df


# ── Sidebar helper ────────────────────────────────────────────────────────────

def render_sidebar() -> None:
    """Consistent sidebar shown on every page."""
    with st.sidebar:
        st.markdown("## 📊 Google Merchandise Store")
        st.markdown("**Funnel Analysis · V4**")
        st.divider()
        st.markdown(
            "**Period:** Nov 2020 – Jan 2021  \n"
            "**Sessions:** 77,020 product-view  \n"
            "**Events:** 4.3 M GA4 events  \n"
            "**Source:** BigQuery public dataset"
        )
        st.divider()
        st.warning(
            "⚠️ **Offline portfolio prototype**  \n"
            "All results are pre-computed from local files. "
            "No BigQuery connection or Google credentials are required.",
            icon=None,
        )
