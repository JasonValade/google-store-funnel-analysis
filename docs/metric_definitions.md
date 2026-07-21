# Metric Definitions

This document defines key terms and metrics used throughout the project. Use these definitions when writing methodology, reproducing results, or building dashboards.

Event
- Definition: A single record in the GA4 export representing an interaction (e.g., page_view, view_item, add_to_cart, purchase).
- Notes: Events have an event_name and may carry nested fields (event_params) and arrays (items).

User
- Definition: Identified by user_pseudo_id in the GA4 export. Acts as an opaque identifier for a visitor across events in this dataset.
- Notes: user_pseudo_id is not personally identifiable information in this obfuscated sample but treat any identifier as sensitive in production.

Session
- Definition: A collection of events grouped into a browsing session. In GA4 export, a session identifier may be available in event_params under the key 'ga_session_id'.
- Implementation used here: session_id = CONCAT(user_pseudo_id, '_', ga_session_id) when ga_session_id exists. Sessions without ga_session_id are labeled '(unknown)'.
- Notes: If ga_session_id is not present, sessionization can be approximated using event_timestamp gaps (e.g., 30-minute inactivity threshold), but that approach is not used by default here.

Transaction / Purchase
- Definition: A purchase is represented by an event where event_name = 'purchase'. A single transaction may contain multiple items.
- Notes: Transaction-level revenue may be recorded in event_params or ecommerce fields on the purchase event; item-level revenue can be computed as SUM(item.price * item.quantity) when these fields are populated.

Funnel entry
- Definition: The funnel entry for this project is `view_item` (a user viewed a product). Depending on the analysis, you may also analyze broader funnels beginning with sessions or page_view events.

Conversion rate
- Definition: The proportion of units that move from one funnel stage A to a subsequent stage B.
- Formula: Conversion rate (A → B) = SAFE_DIVIDE(count_reached_B, count_reached_A)
- Units: conversion rates can be calculated on users, sessions, events, or transactions. Always state the unit used (e.g., user-level conversion).

Drop-off rate
- Definition: Proportion of units that do not progress from stage A to stage B.
- Formula: Drop-off = 1 - Conversion rate (A → B)

Purchase
- Definition: See Transaction / Purchase. For modeling targets, a purchase label is set when a purchase event occurs within the label window.

Revenue
- Definitions:
  - Item revenue: SUM(item.price * item.quantity) for purchase events where item.price and item.quantity are available. Represents revenue attributable to items only.
  - Transaction revenue: Revenue reported at the transaction/purchase event level (may include tax, shipping, discounts). Extract from event-level params (e.g., purchase_revenue, value) if present.
- Guidance: Run `sql/00_schema_inspection.sql` to confirm which revenue fields are present and which to use. Do not estimate transaction revenue from unrelated event parameters.

Traffic source
- Definition: The top-level fields traffic_source.source and traffic_source.medium in this GA4 export are typically populated to reflect first-user acquisition (the source/medium that brought the user). Treat these fields as first-user acquisition fields by default for analyses that compare cohorts by acquisition source.
- Attribution scope: Do NOT assume these fields represent session-level attribution. Before interpreting them as session attribution, check for session-level campaign parameters or a collected_traffic_source field in event_params or other session attributes using `sql/00_schema_inspection.sql`.
- Guidance: Inspect event_param keys and traffic_source fields using `sql/00_schema_inspection.sql`. If session-level campaign parameters are present and populated per session, document that you will use session-level attribution; otherwise, default to first-user acquisition semantics and state that choice in any report.

## Product Analysis

### Product-level aggregation methodology

- **Unit of analysis**: Sessions. Product-view sessions and purchase sessions are counted as distinct sessions using CONCAT(user_pseudo_id, '_', ga_session_id) as the session identifier.
- **Product key**: Normalized product names (LOWER(TRIM(item.item_name))) are used to match product views with purchases because:
  - Item IDs alone were unreliable (810 distinct item IDs in purchase events vs. 427 in view_item events)
  - Normalized names covered 93.55% of product-view sessions and 96.19% of purchase sessions
  - 388 normalized names appeared in both event types; 34 appeared only in views; 8 appeared only in purchases
- **Revenue calculation**: Prefer item.item_revenue when available. Fallback: item.price * item.quantity. Do not mix item-level and transaction-level revenue.
- **Minimum threshold**: Products must have ≥1,000 product-view sessions to reduce noise from low-traffic items.

### Opportunity status field

- **"Investigate availability or tracking"**: Products with zero purchases. Possible causes include unavailable items, discontinued SKUs, catalog changes, data obfuscation, or tracking problems. Not automatically proof of poor product design.
- **"High-traffic, low-conversion candidate"**: Products with purchase rate < 1% and ≥1,000 views. Candidates for further investigation (A/B testing, UX review, qualitative research).
- **"Monitor"**: Products with purchase rate ≥1%. Performing at acceptable baseline for the store.

---

## V3 Purchase-Propensity Model Metrics

The following metrics are used in `notebooks/03_purchase_prediction.ipynb`. The model predicts the probability that a product-view session will result in a purchase.

### Chronological train / validation / test split

- **Definition:** The dataset is divided into three non-overlapping date ranges based on `session_date`, not by random sampling. This preserves temporal order so that the model cannot learn from future sessions.
- **Split dates used in V3:**
  - Train: 2020-11-01 through 2020-12-31 (53,917 sessions, 6.71% purchase rate)
  - Validation: 2021-01-01 through 2021-01-15 (9,445 sessions, 4.04% purchase rate)
  - Test: 2021-01-16 through 2021-01-31 (13,658 sessions, 5.04% purchase rate)
- **Why chronological:** A random split would allow the model to train on sessions from the same days as test sessions, underestimating real-world temporal drift and overstating generalisation performance.
- **Notes:** All preprocessing (imputers, encoders, scalers) is fitted on the training split only and applied to validation and test without refitting.

### Prevalence / no-skill PR-AUC baseline

- **Definition:** The fraction of sessions in a given split that have a positive target (`purchased_later_in_session = 1`). Also the expected precision of a classifier that randomly assigns the positive label, and therefore equal to the no-skill PR-AUC baseline.
- **Formula:** `prevalence = positive_count / total_count`
- **V3 values:** train 6.71%, validation 4.04%, test 5.04% (test no-skill baseline = 0.0504).
- **Notes:** Declining purchase rates across the three splits reflect temporal conversion drift, not a data error.

### PR-AUC (Average Precision — primary metric)

- **Definition:** Area under the Precision-Recall curve, computed as the weighted mean of precisions at each recall threshold (equivalent to `average_precision_score` in scikit-learn). Summarises the trade-off between precision and recall across all classification thresholds.
- **Why primary:** Purchases are rare (~5–7% of sessions). ROC-AUC is inflated by the large number of true negatives. PR-AUC penalises false positives more directly and better reflects model usefulness in an imbalanced setting.
- **No-skill baseline:** Equal to the positive class prevalence in the evaluated split.
- **V3 test result:** 0.1402 vs. 0.0504 no-skill baseline.

### ROC-AUC

- **Definition:** Area under the Receiver Operating Characteristic curve. Probability that the model ranks a randomly chosen positive example above a randomly chosen negative example.
- **Range:** 0.5 (no-skill random classifier) to 1.0 (perfect).
- **V3 test result:** 0.7876.
- **Notes:** Reported as a secondary metric. Interpret alongside PR-AUC; ROC-AUC alone can appear strong even when precision at high recall is poor for imbalanced targets.

### Brier score

- **Definition:** Mean squared error between predicted probabilities and binary outcomes: `mean((p_i − y_i)²)`.
- **Range:** 0 (perfect calibration and discrimination) to 1. Lower is better.
- **No-skill baseline:** Equal to `prevalence × (1 − prevalence)`.
- **V3 test results:** Uncalibrated RF: 0.1778; sigmoid-calibrated RF: 0.0457.
- **Notes:** Class weighting distorts raw probability estimates, causing high uncalibrated Brier scores. Sigmoid calibration substantially improves probability reliability without altering model ranking.

### Precision

- **Definition:** Of all sessions the model flags as likely purchasers at the chosen threshold, the fraction that actually purchased.
- **Formula:** `TP / (TP + FP)`
- **V3 test result (threshold 0.0892):** 0.1578.
- **Notes:** Precision is inherently limited when the positive class is rare. A Brier score or PR-AUC provides a more complete picture than precision alone.

### Recall

- **Definition:** Of all sessions that actually resulted in a purchase, the fraction that the model correctly identified at the chosen threshold.
- **Formula:** `TP / (TP + FN)`
- **V3 test result (threshold 0.0892):** 0.3183.

### F1 score

- **Definition:** Harmonic mean of precision and recall.
- **Formula:** `2 × (precision × recall) / (precision + recall)`
- **V3 test result:** 0.2110.
- **Notes:** The classification threshold was chosen on the validation set by maximising F1 on calibrated validation probabilities. The test threshold is the locked validation threshold (0.0892) and was not re-optimised on test data.

### Confusion matrix

- **Definition:** A 2×2 table showing true positives (TP), true negatives (TN), false positives (FP), and false negatives (FN) at the chosen classification threshold.
- **Rows:** Actual class (0 = did not purchase, 1 = purchased).
- **Columns:** Predicted class at threshold.
- **V3 test result (threshold 0.0892):** TN=11,801 · FP=1,169 · FN=469 · TP=219.

### Top-decile lift

- **Definition:** Ratio of the purchase rate in the highest-scoring 10% of sessions to the overall purchase rate.
- **Formula:** `purchase_rate_in_top_decile / overall_purchase_rate`
- **Interpretation:** A lift of 3.13× means that sessions in the top decile convert at 3.13 times the average rate. Useful for prioritising outreach or targeting.
- **V3 test result:** 3.13×.

### Top-decile capture rate (purchase capture)

- **Definition:** The percentage of all purchases in the test set that fall within the top-scoring 10% of sessions.
- **Formula:** `purchases_in_top_decile / total_purchases × 100`
- **Interpretation:** A capture rate of 31.2% means that by targeting the top decile only, one would reach 31.2% of all purchasers.
- **V3 test result:** 31.2%.

### Probability calibration

- **Definition:** A calibrated model is one whose predicted probability of P% corresponds to an actual positive rate of approximately P% among sessions assigned that score. Assessed visually with a calibration curve (reliability diagram) and quantitatively with the Brier score.
- **Method used in V3:** Sigmoid (Platt scaling) calibration via `CalibratedClassifierCV` with `FrozenEstimator`. The underlying Random Forest is fitted on training data and frozen; the calibration layer is fitted on validation data only using `(X_validation, y_validation)`. Test data is never used for fitting or calibration.
- **Why needed:** `class_weight="balanced_subsample"` improves recall on the minority class but pushes predicted probabilities away from the true positive rate. Sigmoid calibration corrects this shift without retraining the underlying model.

### Validation-selected threshold

- **Definition:** The classification threshold (cut-point on predicted probability) chosen to convert continuous probability scores into binary predictions (purchase / no purchase). In V3 the threshold is selected by evaluating all candidate thresholds on calibrated validation probabilities and choosing the value that maximises F1 on the validation set.
- **V3 calibrated threshold:** 0.0892.
- **Rules:** (1) Threshold is selected using only validation data. (2) The same threshold is applied unchanged to the test set. (3) Test performance is not used to refine the threshold in any way.

