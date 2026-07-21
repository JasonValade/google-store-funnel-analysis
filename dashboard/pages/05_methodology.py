"""
05_methodology.py — Methodology & Limitations page.

Provides full transparency about the analytical approach, data sources,
modelling decisions, and limitations of this portfolio project.
"""

import sys
from pathlib import Path

import streamlit as st

_DASH = Path(__file__).resolve().parent.parent
if str(_DASH) not in sys.path:
    sys.path.insert(0, str(_DASH))

from utils.data_loader import load_model_features, render_sidebar

render_sidebar()
features_df = load_model_features()
metadata_missing_mask = (
    features_df["first_item_price"].isna()
    | (features_df["first_item_name"] == "(unknown)")
    | features_df["first_item_category"].isna()
    | (features_df["first_item_category"] == "(unknown)")
)
metadata_missing_count = int(metadata_missing_mask.sum())
metadata_missing_pct = metadata_missing_count / len(features_df) * 100

st.title("📋 Methodology & Limitations")
st.caption("Transparency on dataset, analytical approach, and known limitations.")
st.divider()

# ── Dataset ────────────────────────────────────────────────────────────────────
st.header("1. Dataset")

st.markdown(
    f"""
    **Source:** `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

    The Google Merchandise Store GA4 e-commerce export is a publicly available,
    obfuscated sample provided by Google for demonstration purposes.

    | Attribute | Value |
    |---|---|
    | Date range | 2020-11-01 to 2021-01-31 (3 months) |
    | Total events | 4,295,584 |
    | Total sessions | 360,129 |
    | Product-view sessions | 77,020 |
    | Data access | BigQuery Sandbox (free, no credit card required) |
    | IAM role required | `roles/bigquery.jobUser` for querying |
    | Dataset path | `bigquery-public-data.ga4_obfuscated_sample_ecommerce` |

    All queries use `_TABLE_SUFFIX` filtering to minimise data scanned.
    SQL scripts are in the `sql/` directory of this repository.
    The repository does not contain Google Cloud credentials or raw BigQuery exports.
    """
)

st.divider()

# ── Funnel methodology ─────────────────────────────────────────────────────────
st.header("2. Funnel Methodology")

st.markdown(
    f"""
    ### Primary ordered funnel
    Sessions are classified as reaching a funnel stage if they contain the
    corresponding GA4 event **in order**: `view_item` → `begin_checkout` → `purchase`.
    A session must contain an earlier stage to be counted in a later stage.

    - **Product-view sessions:** 77,020 — sessions with at least one `view_item` event.
    - **Checkout sessions:** 10,770 — product-view sessions that also contain `begin_checkout`.
    - **Purchase sessions:** 4,661 — checkout sessions that also contain `purchase`.

    This three-stage funnel covers the full Nov 2020 – Jan 2021 period.

    ### Clean cart funnel (4-stage)
    The four-stage funnel (`view_item → add_to_cart → begin_checkout → purchase`)
    is restricted to **Nov 25 – Jan 31** because `add_to_cart` tracking was
    unreliable or absent earlier in November (see Tracking Health Monitor).

    Restricting to the reliable tracking period: 61,835 product-view sessions.

    ### Weekly conversion
    The first row in `weekly_conversion.csv` (week of 2020-10-26) is a partial
    week because GA4 data starts 2020-11-01. It is excluded from trend charts
    by default.

    ### Device comparison
    Device-level conversion rates are compared using a two-proportion z-test
    (mobile vs. desktop). The observed difference (0.35 pp) was borderline
    significant (p = 0.050) and small in practical effect size.
    Tablet sessions (1,700) were too few for a meaningful comparison.
    """
)

st.divider()

# ── Tracking health monitor ────────────────────────────────────────────────────
st.header("3. Tracking Health Monitor")

st.markdown(
    """
    The tracking monitor computes a **rolling 7-day expected baseline** for each
    event type and flags dates where observed counts deviate significantly.

    **Algorithm:**
    1. For each date and event, compute `expected_count` = mean of the same event
       over the preceding 7 days (excluding the alert date).
    2. Compute `event_volume_ratio` = `observed / expected`.
    3. Compute `page_view_ratio` = `observed_page_views / expected_page_views`
       as a proxy for overall site traffic.
    4. Compute `traffic_adjusted_event_ratio` = `event_volume_ratio / page_view_ratio`.
       Values near 1.0 after adjustment indicate the event drop mirrors a traffic drop.

    **Classification:**
    - `CRITICAL_TRACKING_OUTAGE`: event count = 0 while page-view traffic persists
      (traffic-adjusted ratio = 0).
    - `LIKELY_TRAFFIC_DECLINE`: event ratio is low but traffic-adjusted ratio
      is ≥ 0.85, consistent with reduced overall traffic rather than an event failure.

    **Prototype status:** This monitor was built and validated offline on historical
    data. It is not connected to a live GA4 stream and does not send operational alerts.
    All results are illustrative.
    """
)

st.divider()

# ── Purchase-propensity model ──────────────────────────────────────────────────
st.header("4. Purchase Propensity Model")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown(
        """
        ### Prediction task
        Given only information available immediately after a session's **first
        `view_item` event**, predict whether that session will contain a `purchase`
        event later.

        - **Unit of analysis:** session (not user, not page view)
        - **Positive label:** `purchased_later_in_session = 1` (4,688 of 77,020 sessions, ~6.1%)
        - **No leakage:** `add_to_cart`, `begin_checkout`, and all post-view signals
          are excluded as features

        ### Chronological splits
        | Split | Period | Sessions | Purchases | Rate |
        |---|---|---:|---:|---:|
        | Train | Nov 1 – Dec 31, 2020 | 53,917 | 3,618 | 6.71% |
        | Validation | Jan 1–15, 2021 | 9,445 | 382 | 4.04% |
        | Test | Jan 16–31, 2021 | 13,658 | 688 | 5.04% |

        Chronological splitting ensures that no future sessions leak into
        training or validation. The validation set is used for model selection
        and threshold calibration only; the test set is evaluated once.
        """
    )

with col_b:
    st.markdown(
        """
        ### Feature engineering
        Applied before sklearn preprocessing:
        - **item_metadata_missing:** binary flag for missing price/name/category
        - **long_pre_view_session:** 1 if latency > 1800 s before first view
        - **log1p transforms:** seconds to first view (capped at 1800 s),
          page views, scrolls, searches, promotion views, engagement events
        - **Cyclic encoding:** hour-of-day (period 24), day-of-week (period 7)

        ### Preprocessing pipelines
        | Branch | Columns | Steps |
        |---|---|---|
        | Categorical | device, country, source, medium, item name, category | Impute (mode) → OHE (min_freq=50) |
        | Price | first_item_price | Impute (median) → log1p |
        | Numeric (RF) | 13 log/cyclic/binary features | pass-through |

        ### Model selection and calibration
        - **DummyClassifier**, **LogisticRegression**, and **RandomForestClassifier**
          compared on validation PR-AUC
        - **RandomForest** selected (val PR-AUC 0.0997 vs. LR 0.0980 — narrow margin)
        - **Sigmoid calibration** (`FrozenEstimator` + `CalibratedClassifierCV`)
          fitted on validation data only; reduces Brier from 0.1778 → 0.0457
        - **Classification threshold 0.0892** selected on calibrated validation
          probabilities to maximise F1; not re-tuned on test data
        """
    )

st.divider()

# ── Limitations ────────────────────────────────────────────────────────────────
st.header("5. Limitations")

st.markdown(
    f"""
    | Limitation | Detail |
    |---|---|
    | **Three-month window** | Nov 2020 – Jan 2021 covers one holiday season. Patterns may differ in other periods. |
    | **Obfuscated data** | Session IDs, user IDs, and some event parameters are obfuscated. We compute an explicit item-metadata-missing flag from `model_features.csv.gz`: `first_item_price` missing OR `first_item_name == '(unknown)'` OR `first_item_category` missing OR `first_item_category == '(unknown)'`. This affects **{metadata_missing_count:,} / {len(features_df):,} sessions ({metadata_missing_pct:.2f}%)**. |
    | **Temporal drift** | The model is trained on Nov–Dec 2020 and tested on Jan 2021. January has a lower purchase rate (5.04% vs. 6.71% in training). Performance on data from different periods is unknown. |
    | **Missing item metadata** | Using the same explicit metadata-missing definition above, {metadata_missing_pct:.2f}% of sessions have incomplete first-item metadata, limiting product-level signal quality. |
    | **Acquisition-source encoding** | The model captures first-session acquisition signals. Returning-user behaviour is proxied by `is_new_visitor`; full multi-session attribution is not available. |
    | **Class imbalance** | ~6.1% positive rate. `class_weight='balanced'` is applied but the model still has limited recall at any reasonable precision threshold. |
    | **No causal interpretation** | All associations are observational. High-propensity sessions may share characteristics that drive purchase intent independently of any intervention. Controlled A/B experiments are required before acting on model scores. |
    | **No production deployment** | This is an offline portfolio prototype. No live scoring pipeline, serving infrastructure, or monitoring system exists. |
    | **Public obfuscated sample** | Results are specific to this dataset and should not be generalised to the real Google Merchandise Store without validation on unobfuscated data. |
    """
)

st.divider()

# ── Repository structure ───────────────────────────────────────────────────────
st.header("6. Repository Structure")

st.markdown(
    """
    Key paths in this repository:

    | Path | Contents |
    |---|---|
    | `sql/` | BigQuery SQL scripts (00–13), run in order |
    | `notebooks/01_statistical_analysis.ipynb` | Device and funnel statistical tests |
    | `notebooks/02_tracking_health_monitor.ipynb` | Tracking health monitor prototype |
    | `notebooks/03_purchase_prediction.ipynb` | Purchase propensity model |
    | `data/processed/demo/` | Pre-computed CSV/JSON artifacts for this dashboard |
    | `images/` | Static PNG charts from notebook runs |
    | `dashboard/` | This Streamlit application |
    | `docs/data_dictionary.md` | Field definitions |
    | `docs/metric_definitions.md` | Metric and rate definitions |

    The repository does **not** contain:
    - Google Cloud credentials or service-account keys
    - Raw BigQuery exports or large data files outside `data/processed/demo/`
    - A serialised model artifact (the fitted model lives only in notebook kernel memory)
    """
)

st.info(
    "This dashboard is an **offline portfolio prototype** demonstrating "
    "data analysis, statistical testing, ML modelling, and Streamlit visualisation. "
    "It does not represent a production analytics system.",
    icon="ℹ️",
)
