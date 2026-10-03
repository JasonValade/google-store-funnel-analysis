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
        try:
            display_path = p.relative_to(_REPO)
        except ValueError:
            display_path = p
        st.error(
            f"Missing artifact: `{display_path}`  \n"
            "Re-run `notebooks/03_purchase_prediction.ipynb` to regenerate "
            "dashboard artifacts."
        )
        st.stop()
    return p


def inject_global_styles() -> None:
    """
    Layer a small set of design tokens and component refinements on top of the
    native Streamlit dark theme (see .streamlit/config.toml). Colors, fonts,
    and base surfaces are left to Streamlit's theming engine; CSS here is
    limited to spacing, hierarchy, and card/tab polish that theming can't set.
    """
    st.markdown(
        """
        <style>
        :root {
            --gsf-border: rgba(148, 163, 184, 0.18);
            --gsf-card-bg: rgba(255, 255, 255, 0.03);
            --gsf-radius-sm: 8px;
            --gsf-radius-md: 12px;
            --gsf-radius-lg: 16px;
            --gsf-space-sm: 0.5rem;
            --gsf-space-md: 1rem;
            --gsf-space-lg: 1.5rem;
            --gsf-shadow: 0 6px 18px rgba(0, 0, 0, 0.18);
        }

        /* ── Layout & spacing ────────────────────────────────────────────── */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1440px;
        }
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
            margin-bottom: var(--gsf-space-sm);
        }

        /* ── Typography scale ───────────────────────────────────────────── */
        h1 { font-size: 2rem; font-weight: 700; letter-spacing: -0.01em; }
        h2 { font-size: 1.4rem; font-weight: 700; letter-spacing: -0.01em; }
        h3 { font-size: 1.15rem; font-weight: 650; }
        p, li, .stMarkdown, label { line-height: 1.6; }
        [data-testid="stCaptionContainer"] { line-height: 1.5; opacity: 0.82; }

        /* ── Sidebar navigation ──────────────────────────────────────────── */
        div[data-testid="stSidebarNav"] a,
        div[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
            border-radius: var(--gsf-radius-sm);
            padding: 0.45rem 0.6rem;
            transition: background 150ms ease;
        }
        div[data-testid="stSidebarNav"] a:hover,
        div[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {
            background: rgba(79, 140, 255, 0.14);
        }

        /* ── Metric cards ────────────────────────────────────────────────── */
        div[data-testid="stMetric"] {
            background: var(--gsf-card-bg);
            border: 1px solid var(--gsf-border);
            border-radius: var(--gsf-radius-md);
            padding: 0.85rem 1rem 0.7rem;
            box-shadow: var(--gsf-shadow);
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.8rem;
            font-weight: 600;
            opacity: 0.72;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.65rem;
            font-weight: 700;
        }
        div[data-testid="stMetricDelta"] {
            font-size: 0.82rem;
            font-weight: 600;
        }

        /* ── Alerts / info boxes ─────────────────────────────────────────── */
        div[data-testid="stAlertContainer"] {
            border-radius: var(--gsf-radius-md);
            box-shadow: var(--gsf-shadow);
        }

        /* ── Tabs ────────────────────────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.35rem;
            border-bottom: 1px solid var(--gsf-border);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 999px 999px 0 0;
            padding: 0.45rem 1rem;
            font-weight: 550;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            font-weight: 700;
        }

        /* ── Section / hero cards (custom HTML used sparingly) ──────────── */
        .section-card {
            background: var(--gsf-card-bg);
            border: 1px solid var(--gsf-border);
            border-radius: var(--gsf-radius-lg);
            padding: 1rem 1.2rem;
            margin-bottom: var(--gsf-space-md);
            box-shadow: var(--gsf-shadow);
        }
        .section-title {
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        .section-subtitle {
            font-size: 0.92rem;
            opacity: 0.82;
            line-height: 1.55;
        }
        .summary-pill {
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            background: rgba(79, 140, 255, 0.16);
            color: #bcd4ff;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }
        .page-hero {
            background: linear-gradient(120deg, rgba(79,140,255,0.16) 0%, rgba(37,99,235,0.10) 100%);
            border: 1px solid rgba(79, 140, 255, 0.22);
            border-radius: var(--gsf-radius-lg);
            padding: 1.1rem 1.3rem;
            margin-bottom: var(--gsf-space-md);
        }
        .page-hero .eyebrow {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            opacity: 0.75;
            font-weight: 700;
        }
        .page-hero .headline {
            font-size: 1.3rem;
            font-weight: 700;
            margin-top: 0.3rem;
        }
        .page-hero .subhead {
            margin-top: 0.4rem;
            opacity: 0.88;
            line-height: 1.55;
            font-size: 0.95rem;
        }

        /* ── Accessibility: visible focus outline ───────────────────────── */
        :focus-visible {
            outline: 2px solid #4f8cff;
            outline-offset: 2px;
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
# Note: Caching disabled for model artifacts to ensure file changes are reflected immediately.
# These files are small (KB scale) and load quickly, so caching provides minimal benefit.

def load_model_metrics() -> dict:
    """36-key JSON. Rates stored as proportions (0–1), e.g. test_pr_auc=0.140."""
    with open(_demo_path("model_metrics.json")) as fh:
        return json.load(fh)


def load_validation_comparison() -> pd.DataFrame:
    """3-row validation table (Dummy, LR, RF). Rates are proportions."""
    return pd.read_csv(_demo_path("model_validation_comparison.csv"))


def load_pr_curves() -> pd.DataFrame:
    """18 k-row long-format precision-recall curves (validation set)."""
    return pd.read_csv(_demo_path("model_pr_curves.csv"))


def load_calibration_curves() -> pd.DataFrame:
    """20-row calibration data (uncalibrated + sigmoid_calibrated, test set)."""
    return pd.read_csv(_demo_path("model_calibration_curves.csv"))


def load_test_deciles() -> pd.DataFrame:
    """10-row decile table (calibrated RF, test set). Rates are proportions."""
    return pd.read_csv(_demo_path("model_test_deciles.csv"))


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
    """Render a consistent, lightweight page header (native-first, minimal CSS)."""
    st.markdown(
        f"""
        <div class="page-hero">
          <div class="eyebrow">{icon} Portfolio insight</div>
          <div class="headline">{title}</div>
          <div class="subhead">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    """Consistent sidebar shown on every page."""
    inject_global_styles()
    with st.sidebar:
        st.markdown("### 📊 Google Merchandise Store")
        st.caption("Funnel Analysis · V4")
        st.divider()
        m1, m2 = st.columns(2)
        m1.metric("Sessions", "77.0K", help="Product-view sessions in the model dataset.")
        m2.metric("Events", "4.30M", help="Total GA4 events, Nov 2020 – Jan 2021.")
        st.caption(
            "**Period:** Nov 2020 – Jan 2021  \n"
            "**Source:** BigQuery public dataset"
        )
        st.divider()
        st.caption(
            "Offline portfolio prototype: pre-computed local artifacts only "
            "(no live BigQuery access, live scoring, or credentials)."
        )
