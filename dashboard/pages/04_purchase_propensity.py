"""
04_purchase_propensity.py — Purchase Propensity Model page.

Presents pre-computed model evaluation results from the offline Random Forest
Purchase Propensity Model. All metrics are loaded from structured JSON/CSV
artifacts — notebook outputs are never parsed.

No live predictions are made on this page.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

_DASH = Path(__file__).resolve().parent.parent
if str(_DASH) not in sys.path:
    sys.path.insert(0, str(_DASH))

from utils.data_loader import (
    load_model_metrics,
    load_validation_comparison,
    load_pr_curves,
    load_calibration_curves,
    load_test_deciles,
    load_logistic_coefficients,
    render_sidebar,
)
from utils.charts import (
    pr_curves_chart,
    calibration_chart,
    decile_chart,
    coefficient_chart,
)

render_sidebar()

st.title("🤖 Purchase Propensity Model")
st.caption(
    "Random Forest · Sigmoid calibration · Chronological test set · "
    "**No live predictions — pre-computed results only**"
)
st.divider()

# ── Load all artifacts ────────────────────────────────────────────────────────
metrics   = load_model_metrics()
val_comp  = load_validation_comparison()
pr_curves = load_pr_curves()
cal_curves = load_calibration_curves()
deciles   = load_test_deciles()
coefs     = load_logistic_coefficients()

# ── KPI cards ─────────────────────────────────────────────────────────────────
st.subheader("Test-Set Performance (Calibrated Random Forest)")
st.caption("Evaluated once on the untouched chronological test set (Jan 16 – Jan 31, 2021).")

k1, k2, k3 = st.columns(3)
k4, k5, k6 = st.columns(3)

k1.metric(
    "Test PR-AUC",
    f"{metrics['test_pr_auc']:.4f}",
    help="Average precision on the chronological test set.",
    delta=f"+{metrics['test_pr_auc']-metrics['test_no_skill_pr_auc']:.4f} vs no-skill",
)
k2.metric(
    "No-skill PR-AUC",
    f"{metrics['test_no_skill_pr_auc']:.4f}",
    help="Baseline equal to test-set prevalence (5.04%).",
)
k3.metric(
    "ROC-AUC",
    f"{metrics['test_roc_auc']:.4f}",
    help="Area under the ROC curve on the test set.",
)
k4.metric(
    "Brier score (calibrated)",
    f"{metrics['test_brier_calibrated']:.4f}",
    help=f"Improved from {metrics['test_brier_uncalibrated']:.4f} (uncalibrated) "
         "after sigmoid calibration.",
    delta=f"{metrics['test_brier_calibrated']-metrics['test_brier_uncalibrated']:.4f} vs uncalibrated",
    delta_color="inverse",
)
k5.metric(
    "Top-decile lift",
    f"{metrics['test_top_decile_lift']:.2f}×",
    help="Purchase rate in the top risk decile ÷ overall test purchase rate.",
)
k6.metric(
    "Top-decile capture",
    f"{metrics['test_top_decile_capture']*100:.1f}%",
    help="Fraction of all test purchases captured in the top-risk decile.",
)

st.divider()

# ── Charts row 1: PR curves + calibration ─────────────────────────────────────
st.subheader("Model Evaluation Charts")

tab_pr, tab_cal, tab_decile, tab_coef = st.tabs([
    "Precision-Recall Curves",
    "Calibration Curves",
    "Risk-Decile Lift",
    "Feature Associations (LR)",
])

with tab_pr:
    st.markdown(
        "**Validation-set precision-recall curves** (uncalibrated probabilities). "
        "Calibration does not alter rank ordering, so PR-AUC values are the same "
        "before and after calibration."
    )
    st.plotly_chart(
        pr_curves_chart(pr_curves, no_skill=metrics["validation_purchases"] / metrics["validation_rows"]),
        width="stretch",
        theme="streamlit",
    )
    st.caption(
        f"LR validation PR-AUC: **{metrics['validation_logistic_pr_auc']:.4f}** · "
        f"RF validation PR-AUC: **{metrics['validation_random_forest_pr_auc']:.4f}** · "
        "Random Forest was selected by validation PR-AUC; its advantage over "
        "logistic regression was narrow."
    )
    with st.expander("ℹ️ Why is PR-AUC preferred over ROC-AUC here?"):
        st.markdown(
            """
            The dataset is heavily class-imbalanced: only ~6% of sessions purchased.
            ROC-AUC can appear high even for weak models on imbalanced data because
            it averages over all classification thresholds. Precision-Recall AUC
            focuses on the minority positive class and is more informative when
            recall of purchasers is the operational goal.
            """
        )

with tab_cal:
    st.markdown(
        "**Calibration curves on the test set** (equal-frequency bins, n = 10). "
        "Well-calibrated probabilities lie close to the diagonal."
    )
    st.plotly_chart(calibration_chart(cal_curves), width="stretch", theme="streamlit")
    col_c1, col_c2 = st.columns(2)
    col_c1.metric("Brier score (uncalibrated)", f"{metrics['test_brier_uncalibrated']:.4f}")
    col_c2.metric("Brier score (calibrated)", f"{metrics['test_brier_calibrated']:.4f}",
                  delta=f"{metrics['test_brier_calibrated']-metrics['test_brier_uncalibrated']:.4f}",
                  delta_color="inverse")
    with st.expander("ℹ️ Calibration method"):
        st.markdown(
            """
            **Sigmoid (Platt) calibration** was fitted on the validation set only
            (`FrozenEstimator` + `CalibratedClassifierCV(method="sigmoid", cv=None)`
            from scikit-learn ≥ 1.4).

            `FrozenEstimator` freezes the underlying Random Forest so that
            calibration fitting cannot re-use test-set information. The threshold
            of **{:.4f}** was selected by maximising F1 on calibrated validation
            probabilities and was not re-tuned on the test set.
            """.format(metrics["calibrated_threshold"])
        )

with tab_decile:
    st.markdown(
        "**Purchase rate by predicted-risk decile** (calibrated RF, test set). "
        "Decile 1 contains sessions with the highest predicted purchase probability."
    )
    st.plotly_chart(decile_chart(deciles), width="stretch", theme="streamlit")

    st.dataframe(
        deciles.assign(
            purchase_rate_pct=(deciles["purchase_rate"] * 100).round(2),
            lift=deciles["lift"].round(3),
        )[["risk_decile", "session_count", "purchase_count",
           "purchase_rate_pct", "lift"]].rename(columns={
            "risk_decile":       "Decile (1=highest risk)",
            "session_count":     "Sessions",
            "purchase_count":    "Purchases",
            "purchase_rate_pct": "Purchase rate %",
            "lift":              "Lift",
        }),
        width="stretch",
        hide_index=True,
    )

with tab_coef:
    st.markdown(
        "**Top-20 Logistic Regression features by absolute coefficient magnitude.** "
        "Coefficients represent associations between early-session signals and "
        "purchase probability in the LR model trained on the same data. "
        "**These are not causal effects — the data is observational.**"
    )
    st.plotly_chart(coefficient_chart(coefs), width="stretch", theme="streamlit")
    st.caption(
        "Display labels are human-readable; hover text preserves raw sklearn feature names. "
        "The LR model was not selected by validation PR-AUC (Random Forest was selected by a "
        "narrow margin), but LR coefficients are useful for directional interpretation."
    )

st.divider()

# ── Validation comparison table ───────────────────────────────────────────────
st.subheader("Validation Model Comparison")
st.caption("Uncalibrated probabilities on the validation set (Jan 1–15, 2021).")

vc_display = val_comp.copy()
for col in ["pr_auc", "roc_auc", "brier_score", "precision", "recall", "f1"]:
    vc_display[col] = vc_display[col].round(4)
vc_display["top_decile_lift"]    = vc_display["top_decile_lift"].round(3)
vc_display["top_decile_capture"] = (vc_display["top_decile_capture"] * 100).round(1)
vc_display["threshold"]          = vc_display["threshold"].round(4)

st.dataframe(
    vc_display.rename(columns={
        "model":              "Model",
        "pr_auc":             "PR-AUC",
        "roc_auc":            "ROC-AUC",
        "brier_score":        "Brier",
        "precision":          "Precision",
        "recall":             "Recall",
        "f1":                 "F1",
        "top_decile_lift":    "Lift@Decile1",
        "top_decile_capture": "Capture@D1 %",
        "threshold":          "Threshold",
    }),
    width="stretch",
    hide_index=True,
)

st.caption(
    f"Random Forest was selected by validation PR-AUC (advantage over logistic "
    f"regression: {metrics['validation_random_forest_pr_auc'] - metrics['validation_logistic_pr_auc']:.4f}). "
    "This gap is narrow and both models performed similarly."
)

st.divider()

# ── Split period table ────────────────────────────────────────────────────────
st.subheader("Chronological Data Splits")
st.caption(
    "Splits were determined by calendar date to prevent data leakage. "
    "No sessions from the validation or test period appear in training."
)

split_data = {
    "Split":      ["Train", "Validation", "Test"],
    "Start":      [metrics["train_start"],      metrics["validation_start"],      metrics["test_start"]],
    "End":        [metrics["train_end"],         metrics["validation_end"],         metrics["test_end"]],
    "Sessions":   [
        f"{metrics['train_rows']:,}",
        f"{metrics['validation_rows']:,}",
        f"{metrics['test_rows']:,}",
    ],
    "Purchases":  [
        f"{metrics['train_purchases']:,}",
        f"{metrics['validation_purchases']:,}",
        f"{metrics['test_purchases']:,}",
    ],
    "Rate %":     [
        round(metrics["train_purchase_rate"] * 100, 2),
        round(metrics["validation_purchase_rate"] * 100, 2),
        round(metrics["test_purchase_rate"] * 100, 2),
    ],
    "Role": [
        "Fit LR + RF pipelines",
        "Model selection by validation PR-AUC · Fit sigmoid calibration · Select threshold",
        "Final one-time evaluation (untouched)",
    ],
}
st.dataframe(pd.DataFrame(split_data), width="stretch", hide_index=True)

st.divider()

# ── Confusion matrix ──────────────────────────────────────────────────────────
st.subheader("Confusion Matrix — Calibrated RF, Test Set")
st.caption(
    f"Classification threshold = **{metrics['calibrated_threshold']:.4f}** "
    "(selected on calibrated validation probabilities to maximise F1)."
)

tn = metrics["confusion_matrix_tn"]
fp = metrics["confusion_matrix_fp"]
fn = metrics["confusion_matrix_fn"]
tp = metrics["confusion_matrix_tp"]

cm_df = pd.DataFrame(
    [[f"TN = {tn:,}", f"FP = {fp:,}"],
     [f"FN = {fn:,}", f"TP = {tp:,}"]],
    index=["Actual: No purchase", "Actual: Purchase"],
    columns=["Predicted: No purchase", "Predicted: Purchase"],
)
st.dataframe(cm_df, width="stretch")

cm1, cm2, cm3 = st.columns(3)
cm1.metric("Precision", f"{metrics['test_precision']:.4f}",
           help="TP / (TP + FP)")
cm2.metric("Recall",    f"{metrics['test_recall']:.4f}",
           help="TP / (TP + FN)")
cm3.metric("F1",        f"{metrics['test_f1']:.4f}",
           help="Harmonic mean of precision and recall.")

st.divider()

# ── Key methodology notes ─────────────────────────────────────────────────────
st.subheader("Methodology Notes")

with st.expander("Feature engineering and leakage prevention"):
    st.markdown(
        """
        **Prediction moment:** immediately after the session's first `view_item` event.
        Only signals observable at or before that moment are used as features.

        **Explicitly excluded to prevent leakage:**
        - `add_to_cart` events (post-view intent signal)
        - `begin_checkout` events (post-view intent signal)
        - Any event counts that occur after the first `view_item`

        **Engineered features include:**
        - Pre-view engagement (page views, scroll events, search events, promotions)
        - Session-start-to-view latency (log-transformed, capped at 1800 s)
        - Item metadata completeness flag
        - Cyclic encoding of hour-of-day and day-of-week
        - Device category, country, acquisition source/medium (OHE, min_frequency=50)
        - First-item name and category (OHE, min_frequency=50)
        - First-item price (log-transformed)
        """
    )

with st.expander("Class weighting and calibration rationale"):
    st.markdown(
        f"""
        **Class imbalance:** ~{metrics['overall_positive_rate']*100:.1f}% of sessions purchased.
        Both LR and RF were fitted with `class_weight='balanced'` /
        `class_weight='balanced_subsample'` to prevent the model from predicting
        "no purchase" for every session.

        **Sigmoid calibration** (Platt scaling) was applied after training to
        convert raw score outputs into reliable probability estimates.
        Without calibration, the RF Brier score was
        **{metrics['test_brier_uncalibrated']:.4f}**; after calibration it dropped to
        **{metrics['test_brier_calibrated']:.4f}**, confirming substantially improved
        probability reliability.
        """
    )

st.info(
    "**Causal interpretation:** This model identifies statistical associations between "
    "early-session signals and session-level purchase events. "
    "It does **not** establish causal relationships. "
    "High propensity scores indicate that sessions with similar early-session "
    "characteristics have historically purchased more often — not that any "
    "intervention will increase conversions. "
    "Controlled experiments are required before acting on model scores.",
    icon="⚠️",
)

st.info(
    "**No live predictions:** This page presents pre-computed evaluation results "
    "from offline notebook runs. The fitted model is not serialised in this "
    "repository and no real-time scoring is performed.",
    icon="ℹ️",
)
