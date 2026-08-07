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


def inject_global_styles() -> None:
    """Apply a polished visual theme across the dashboard pages."""
    st.markdown(
        """
        <style>
        :root {
            color-scheme: dark;
        }
        .stApp {
            background: linear-gradient(135deg, #07111f 0%, #0b1727 48%, #111c2f 100%);
            color: #f8fafc;
        }
        .stApp, .stApp p, .stApp div, .stApp span, .stApp label, .stApp a,
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp .stMarkdown,
        .stApp .stTextInput, .stApp .stSelectbox, .stApp .stMultiSelect,
        .stApp .stButton, .stApp .stDownloadButton, .stApp .stDataFrame {
            color: #f8fafc !important;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }
        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #06111f 0%, #0f1b30 100%);
            border-right: 1px solid rgba(148, 163, 184, 0.16);
        }
        div[data-testid="stSidebar"] * {
            color: #f8fafc !important;
        }
        div[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
            border-radius: 10px;
            padding: 0.45rem 0.6rem;
            transition: background 180ms ease;
        }
        div[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {
            background: rgba(79, 140, 255, 0.16);
        }
        .stMetric {
            background: rgba(10, 21, 37, 0.96);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 14px;
            padding: 0.7rem 0.85rem;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
        }
        .stMetric [data-testid="stMetricValue"] {
            color: #f8fafc !important;
        }
        .stAlert, .stInfo, .stSuccess, .stWarning {
            border-radius: 12px;
            border: 1px solid rgba(79, 140, 255, 0.2);
            background: rgba(10, 21, 37, 0.96);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.18);
        }
        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stSelectbox > div > div > div,
        .stMultiSelect > div > div > div,
        .stDateInput > div > div > div {
            background: rgba(7, 16, 31, 0.95) !important;
            color: #f8fafc !important;
            border: 1px solid rgba(148, 163, 184, 0.24) !important;
            border-radius: 10px !important;
        }
        .stButton > button, .stDownloadButton > button {
            background: linear-gradient(90deg, #4f8cff 0%, #2563eb 100%);
            color: white !important;
            border: none;
            border-radius: 999px;
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.28);
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            background: linear-gradient(90deg, #60a5fa 0%, #3b82f6 100%);
        }
        h1, h2, h3 {
            letter-spacing: -0.02em;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.4rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding: 0.4rem 0.8rem;
            border: 1px solid rgba(79, 140, 255, 0.2);
            background: rgba(17, 28, 47, 0.75);
            color: #f8fafc;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(90deg, #4f8cff 0%, #2563eb 100%);
            color: white;
            border-color: #4f8cff;
        }
        .section-card {
            background: rgba(10, 21, 37, 0.96);
            border: 1px solid rgba(79, 140, 255, 0.2);
            border-radius: 16px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        }
        .section-title {
            font-size: 1rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 0.25rem;
        }
        .section-subtitle {
            font-size: 0.92rem;
            color: #cbd5e1;
            line-height: 1.45;
        }
        .summary-pill {
            display: inline-block;
            padding: 0.28rem 0.6rem;
            border-radius: 999px;
            background: rgba(79, 140, 255, 0.15);
            color: #bfdbfe;
            font-size: 0.78rem;
            font-weight: 600;
            margin-bottom: 0.45rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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

def render_page_header(title: str, subtitle: str, icon: str = "📊") -> None:
    """Render a polished hero section at the top of each dashboard page."""
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #111c2f 0%, #1e3a8a 50%, #4f8cff 100%);
        border-radius: 18px; padding: 1.2rem 1.3rem; color: white;
        box-shadow: 0 14px 36px rgba(0, 0, 0, 0.24); margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.08);">
          <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.2em; opacity: 0.9;">
            {icon} Portfolio insight
          </div>
          <div style="font-size: 1.24rem; font-weight: 700; margin-top: 0.3rem;">
            {title}
          </div>
          <div style="margin-top: 0.4rem; opacity: 0.95; line-height: 1.5;">
            {subtitle}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    """Consistent sidebar shown on every page."""
    inject_global_styles()
    with st.sidebar:
        st.markdown("## 📊 Google Merchandise Store")
        st.markdown("**Funnel Analysis · V4**")
        st.divider()
        st.markdown(
            "**Period:** Nov 2020 – Jan 2021  \n"
            "**Sessions:** 77,020 product-view  \n"
            "**Events:** 4,295,584 GA4 events  \n"
            "**Source:** BigQuery public dataset"
        )
        st.caption(
            "Offline portfolio prototype: pre-computed local artifacts only "
            "(no live BigQuery access, live scoring, or credentials)."
        )
