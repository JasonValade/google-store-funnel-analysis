# Purchase-Propensity Model Methodology

**Author:** Jason Valade  
**Dataset:** `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*` (November 2020 – January 2021)  
**Notebook:** `notebooks/03_purchase_prediction.ipynb`  
**Feature SQL:** `sql/09_model_features.sql`  
**Feature validation SQL:** `sql/13_model_feature_validation.sql`  
**Data dictionary:** `docs/data_dictionary.md`  
**Metric definitions:** `docs/metric_definitions.md`

---

## 1. Executive Summary

This report documents a session-level purchase-propensity model trained on the public Google Merchandise Store GA4 export. The model predicts whether a session that has just viewed a product will result in a purchase later in that same session, using only information available at the moment of the first product view.

**What this model can and cannot support:**

- **Can support:** Ranking sessions by purchase propensity at the first product view, which can inform capacity-constrained targeting decisions (e.g., allocating limited outreach resources to sessions most likely to convert).
- **Can support:** Identifying statistical associations between early-session signals and purchase outcomes, which can generate hypotheses for further investigation.
- **Cannot support:** Causal claims about why sessions convert. Differences in predicted probability reflect associations, not causal effects.
- **Cannot support:** Predictions about incremental treatment response. The model estimates baseline purchase propensity, not how sessions would respond to an intervention.
- **Cannot support:** Profitability optimization without additional information on intervention costs, customer lifetime value, and incremental conversion effects.

**Key findings:**

- The model achieved a test-set PR-AUC of **0.1402** on 13,658 held-out sessions, compared to a no-skill baseline of **0.0504** (the test-set purchase prevalence).
- The highest-scoring decile of sessions converted at **15.74%**, representing a **3.12× lift** over the overall test purchase rate of **5.04%**.
- The top decile captured **31.3% of all test purchases** (215 of 688 purchases; 215/688 = 31.25%, displayed as 31.3%) despite containing only 10% of sessions.
- Random Forest was selected over logistic regression by a narrow observed validation PR-AUC margin (0.0997 vs. 0.0980), with both models showing similar performance. This small advantage does not establish general superiority.
- The calibrated model had a lower Brier score on the held-out test set: 0.0457 versus 0.1778 for the uncalibrated class-weighted model. Calibration was fitted on validation data and evaluated once on test data.

---

## 2. Purchase-Rate Contexts and Populations

Three different purchase-rate values appear in this project. Each reflects a different population and definition. Understanding these distinctions is essential for correct interpretation.

| Context | Purchase Rate | Numerator | Denominator | Population Definition | Date Range | Source |
|---------|---------------|-----------|------------|----------------------|------------|--------|
| **Ordered funnel conversion** | 6.05% | 4,661 sessions with all four funnel events in strict order | 77,020 sessions with a view_item event | Sessions that completed the full ordered funnel: view_item → add_to_cart → begin_checkout → purchase (strict timestamp order) | Nov 2020 – Jan 2021 | `sql/05_ordered_session_funnel.sql`, notebook `01_statistical_analysis.ipynb` |
| **Model dataset prevalence** | 6.09% | 4,688 sessions with purchase strictly after first view_item | 77,020 sessions with a view_item event | Sessions with purchase occurring **strictly after** the first view_item timestamp (model target definition) | Nov 2020 – Jan 2021 | `data/processed/demo/model_metrics.json` (dataset_positive_sessions / dataset_rows) |
| **Test-set prevalence** | 5.04% | 688 sessions with purchase strictly after first view_item | 13,658 sessions in the test split | Model dataset restricted to the chronological test window (Jan 16–31, 2021) | Jan 16–31, 2021 | `data/processed/demo/model_metrics.json` (test_purchases / test_rows) |

**Why the values differ:**

- **6.05% vs. 6.09% (27-session difference):** The ordered funnel (4,661) counts only sessions that completed all four funnel stages in strict timestamp order: view_item → add_to_cart → begin_checkout → purchase. The model dataset (4,688) counts all sessions with a purchase event strictly after the first view_item, regardless of whether they went through begin_checkout or add_to_cart. The 27-session difference (4,688 - 4,661) represents sessions that purchased without completing the full ordered funnel (e.g., purchased directly, or events occurred out of order).
- **6.09% vs. 5.04% (temporal drift):** The model dataset spans the full three-month period (Nov–Jan), while the test set covers only the final two weeks (Jan 16–31). Purchase rates declined over time (6.71% in train, 4.04% in validation, 5.04% in test), reflecting temporal conversion drift. The test-set prevalence of 5.04% is the relevant baseline for evaluating model performance on held-out data.

**Important:** When referring to "overall purchase rate" in this report, it always specifies the population (e.g., "test-set purchase rate of 5.04%"). The 6.05% funnel conversion is a separate descriptive metric for the overall funnel and is not the model's test prevalence.

---

## 3. Decision Context and Prediction Question

The model addresses a practical business question: **Given that a visitor has just viewed a product, which sessions are most likely to result in a purchase?**

This prediction problem is motivated by several operational scenarios:

- **Targeted outreach:** Limited customer-service or sales capacity can be allocated to visitors with the highest predicted purchase probability.
- **Prioritized analysis:** Analysts can focus qualitative research or usability testing on sessions that the model identifies as high-propensity but do not convert.
- **Experiment stratification:** Propensity scores can be used to balance treatment and control groups in randomized experiments.
- **Funnel diagnostics:** Understanding which early-session signals correlate with purchases can highlight product, UX, or merchandising hypotheses for further investigation.

The prediction is made **immediately after the session's first `view_item` event**. This timing is chosen because:

1. It is the earliest moment when product interest is clearly signaled.
2. It maximizes the window for potential intervention (e.g., live chat, targeted offers).
3. It aligns with practical operational constraints—interventions typically occur during or shortly after product viewing.

The model does **not** predict whether an intervention will increase conversion. It predicts which sessions, *in the absence of intervention*, have historically been more likely to purchase based on observable early-session characteristics.

---

## 4. Unit of Observation and Eligible Session Population

**Unit of observation:** One GA4 session containing at least one `view_item` event.

**Session definition:** `session_id = CONCAT(user_pseudo_id, '_', CAST(ga_session_id AS STRING))`. Sessions without a valid `ga_session_id` are excluded.

**Eligibility criteria:** A session is eligible for modeling if:

1. It contains at least one `view_item` event.
2. The `session_id` can be constructed (i.e., both `user_pseudo_id` and `ga_session_id` are present).
3. The session falls within the analyzed date range (November 1, 2020 – January 31, 2021).

**Population size:** The eligible population contains **77,020 sessions**. This represents a subset of the full GA4 export, filtered to sessions that reached the product-view stage.

**Rationale for this unit:** Session-level prediction is appropriate when the intervention opportunity occurs during a browsing session. User-level prediction would require tracking behavior across multiple sessions, which introduces additional complexity (e.g., cross-session attribution, varying time horizons) that is beyond the scope of this project.

---

## 5. Outcome Definition and Class Prevalence

**Target variable:** `purchased_later_in_session`

**Definition:** Binary indicator equal to 1 if a `purchase` event occurs **strictly after** the session's first `view_item` timestamp, and 0 otherwise.

**Temporal scope:** The entire remainder of the session is used as the observation window. No fixed time window (e.g., 10 minutes) is imposed. If a purchase occurs at any point after the first product view within the same session, the session is labeled as positive.

**Class prevalence across the full model dataset:**

\[
\text{Purchase prevalence} = \frac{\text{Number of sessions with purchase strictly after first view}}{\text{Total eligible sessions}} = \frac{4,688}{77,020} = 0.0609 \text{ (6.09%)}
\]

The outcome is **imbalanced**: approximately 94% of sessions do not result in a purchase. This imbalance justifies the use of PR-AUC as the primary evaluation metric, as discussed in Section 15.

**Outcome vs. target:** The term "outcome" refers to the actual behavior (purchase or no purchase). The term "target" refers to the variable used in model training. In this report, they are equivalent.

---

## 6. Prediction Timing at the First `view_item`

**Prediction moment:** Immediately after the session's first `view_item` event.

**Implementation:** The first `view_item` timestamp is identified per session:

```sql
first_view_item_timestamp = MIN(event_timestamp)
WHERE event_name = 'view_item'
```

All features are constructed using only information available at or before this timestamp. Features using information from after this moment are explicitly excluded to prevent leakage.

**Why this timing:**

- **Early actionability:** Interventions such as live chat, personalized offers, or targeted messaging are most effective when initiated during the browsing session.
- **Clear intent signal:** The first product view is an unambiguous indicator of interest in a specific item.
- **Maximizes observation window:** By predicting at the first view, the model has the full remainder of the session to observe whether a purchase occurs.

**Alternative timing considered and rejected:**

- **At session start:** Too early—no product interest has been signaled, and most sessions do not view any product.
- **At `add_to_cart`:** Too late—this is a strong intent signal that would trivialize the prediction task and is not reliably tracked during parts of the period.
- **At `begin_checkout`:** Too late—visitors at this stage are already highly likely to purchase, and intervention opportunities are limited.

---

## 7. Feature Construction and Availability

All features are extracted from the GA4 export using `sql/09_model_features.sql`. The pipeline enforces a strict temporal boundary: **no feature may use information from after `first_view_item_timestamp`**.

### 7.1 Feature Categories

**Device and geography:**
- `device_category`: Desktop, mobile, tablet (or unknown)
- `country`: Visitor's country from GA4 geo record (or unknown)

**Acquisition (first-user):**
- `acquisition_source`: First-user acquisition source (e.g., google, direct, youtube)
- `acquisition_medium`: First-user acquisition medium (e.g., organic, cpc, referral)

**Important caveat:** These fields reflect **first-user acquisition**—how the user was originally brought to the store—not the source of the current session. They should not be interpreted as session-level attribution.

**Product information (from the first `view_item` event):**
- `first_item_name`: Normalized name of the first item in the items array
- `first_item_category`: Category of the first item
- `first_item_price`: Listed price of the first item (may be null)

**Temporal features:**
- `hour_of_day`: Hour (0–23) of the first `view_item` in UTC
- `day_of_week`: Day of week (1 = Sunday … 7 = Saturday)
- `seconds_from_session_start_to_first_view`: Elapsed seconds between session start and first product view

**Pre-view behavioral counts:**
- `page_views_before_first_view`: Count of page views before the first product view
- `scroll_events_before_first_view`: Count of scroll events before the first product view
- `search_events_before_first_view`: Count of search events before the first product view
- `promotion_views_before_first_view`: Count of promotion views before the first product view
- `engagement_events_before_first_view`: Count of user engagement events before the first product view

**Visitor status:**
- `is_new_visitor`: 1 if a `first_visit` event occurred at or before the first product view, 0 otherwise

### 7.2 Engineered Features

The notebook applies deterministic transformations to raw features:

**Missingness indicators:**
- `item_metadata_missing`: Binary flag when price is null, item name is "(unknown)", or category is missing

**Capping and transformation:**
- `seconds_from_session_start_to_first_view` is capped at 1,800 seconds (30 minutes) to prevent outliers from dominating linear models
- Capped seconds are transformed with `log1p` (log(1 + x)) to compress the right-skewed distribution
- Count features are transformed with `log1p` for the same reason

**Cyclic encoding:**
- `hour_of_day` is encoded as sine/cosine components with period 24 to preserve circular time structure (23:00 is adjacent to 00:00)
- `day_of_week` is encoded as sine/cosine components with period 7

**One-hot encoding:**
- Categorical features (`device_category`, `country`, `acquisition_source`, `acquisition_medium`, `first_item_name`, `first_item_category`) are one-hot encoded with a minimum frequency threshold of 50. Categories appearing fewer than 50 times in the training set are grouped into an "infrequent" bucket.

### 7.3 Feature Availability

All features are available at the prediction moment by construction:

- Device and geography are reported by GA4 for each event
- Acquisition fields are user-level attributes available from session start
- Product information comes from the `view_item` event itself
- Temporal features are derived from the `view_item` timestamp
- Behavioral counts are aggregated from events with `event_timestamp < first_view_item_timestamp`

No feature requires future information or post-view behavior.

---

## 8. Leakage Prevention

Data leakage occurs when the model has access to information that would not be available at prediction time in a real deployment. This section documents the specific steps taken to prevent leakage.

### 8.1 Temporal Leakage Prevention

**Strict timestamp boundary:** All event-count features use the condition `event_timestamp < first_view_item_timestamp` (strict less-than). This ensures that no events occurring at or after the prediction moment are included.

**Explicitly excluded post-view events:**
- `add_to_cart` events: These are strong intent signals that occur after product viewing. Including them would trivialize the prediction task.
- `begin_checkout` events: Similarly, these occur after the prediction moment and would leak future intent.
- `purchase` events: The target itself is constructed from these events, but they are never used as features.

**No observation window artifacts:** Earlier versions of the model used a fixed ten-minute observation window. This was replaced with the strict timestamp rule to avoid arbitrary cutoffs and ensure full session coverage.

### 8.2 Target Leakage Prevention

**Target not used as feature:** The `purchased_later_in_session` variable is never included in the feature set.

**No derived targets:** Features that would directly encode the target (e.g., "has purchased before") are excluded. Only pre-view behavioral counts are used.

### 8.3 Train-Test Leakage Prevention

**Chronological splitting:** Sessions are split by calendar date rather than randomly shuffled. This prevents the model from learning patterns specific to a time period that would not generalize forward.

**Preprocessing fitted on training only:** Imputers, encoders, and scalers are fitted on the training split only. The fitted transformations are then applied to validation and test splits without refitting.

**Calibration on validation only:** Sigmoid calibration is fitted on the validation set using `FrozenEstimator`, which prevents the calibration layer from accessing test data.

**Threshold selection on validation only:** The classification threshold is selected by maximizing F1 on calibrated validation probabilities. The same threshold is then applied to the test set without re-optimization.

### 8.4 Validation

The SQL query `sql/13_model_feature_validation.sql` was used to verify that:
- All event counts respect the timestamp boundary
- No post-view events appear in feature aggregations
- The first item details are consistently extracted from the first `view_item` event only

---

## 9. Chronological Train, Validation, and Held-Out Test Design

The dataset is divided into three non-overlapping chronological windows based on `session_date`. No random shuffling is used.

### 9.1 Split Definitions

| Split      | Date Range          | Sessions | Purchases | Purchase Rate |
|------------|---------------------|----------|-----------|---------------|
| Train      | 2020-11-01 → 2020-12-31 | 53,917   | 3,618     | 6.71%         |
| Validation | 2021-01-01 → 2021-01-15 | 9,445    | 382       | 4.04%         |
| Test       | 2021-01-16 → 2021-01-31 | 13,658   | 688       | 5.04%         |

**Total:** 77,020 sessions, 4,688 purchases, 6.09% overall purchase rate.

### 9.2 Purpose of Each Split

**Train split:** Used to fit the models (logistic regression and random forest), preprocessors (imputers, encoders, scalers), and learn model parameters.

**Validation split:** Used for:
- Model selection (comparing logistic regression vs. random forest by PR-AUC)
- Fitting the sigmoid calibration layer
- Selecting the classification threshold by maximizing F1 on calibrated probabilities

**Test split:** Used **once** for final evaluation. The test set is never used during model fitting, calibration, or threshold selection. All test metrics reported in this report are from this held-out split.

### 9.3 Why Chronological Splitting

**Temporal realism:** In production, a model will be applied to future data. A chronological split simulates this scenario and provides a realistic estimate of temporal generalization.

**Prevents leakage:** Random splitting would allow the model to train on sessions from the same days as test sessions, potentially learning day-specific patterns that would not generalize to new time periods.

**Detects drift:** The declining purchase rates across splits (6.71% → 4.04% → 5.04%) reflect temporal conversion drift. A chronological split captures this drift and ensures the model is evaluated on a different conversion environment.

### 9.4 Non-Overlap Verification

The notebook confirms that no session appears in more than one split:

```python
assert len(set(train["session_id"]) & set(val["session_id"])) == 0
assert len(set(val["session_id"]) & set(test["session_id"])) == 0
```

---

## 10. Preprocessing and Missing-Data Handling

Preprocessing is implemented as a scikit-learn `Pipeline` to ensure consistent application across train, validation, and test splits.

### 10.1 Missing Data

**Missing values in raw data:**
- `first_item_category`: 2,187 missing (2.84% of sessions)
- `first_item_price`: 20,697 missing (26.87% of sessions)

**Handling strategy:**
- Numerical features: `SimpleImputer(strategy="median")` fills missing values with the median from the training split
- Categorical features: `SimpleImputer(strategy="most_frequent")` fills missing values with the most frequent category from the training split
- One-hot encoding: The `(unknown)` category is used as the fill value for missing categories

**Missingness as signal:** The engineered feature `item_metadata_missing` explicitly captures whether item metadata is incomplete, allowing the model to use missingness as a predictive signal rather than simply imputing it away.

### 10.2 Feature Scaling

**StandardScaler:** Applied to numerical features (log-transformed counts, capped seconds, price) to standardize them to zero mean and unit variance. This is necessary for logistic regression, which is sensitive to feature scale.

**Tree-based models:** Random Forest does not require feature scaling, but the same preprocessing pipeline is applied for consistency and to enable fair model comparison.

### 10.3 Categorical Encoding

**OneHotEncoder:** Applied to categorical features with `handle_unknown="infrequent_if_exist"`. Categories that appear in the test set but not in the training set are grouped into an "infrequent" bucket rather than causing errors.

**Minimum frequency threshold:** Categories appearing fewer than 50 times in the training set are grouped into "infrequent" to prevent overfitting to rare categories and reduce dimensionality.

### 10.4 Deterministic Feature Engineering

Feature engineering transformations (capping, log transforms, cyclic encoding) are **deterministic**—they do not involve computing statistics from the data. These transformations are applied identically to all splits without fitting.

---

## 11. Candidate Models and Selection Criteria

### 11.1 Candidate Models

**Logistic Regression:**
- Linear model with L2 regularization
- Interpretable coefficients provide directional associations
- Serves as a strong baseline and a reference for feature importance

**Random Forest:**
- Non-linear ensemble of decision trees
- Can capture complex interactions without explicit feature engineering
- Robust to outliers and irrelevant features

**Dummy Classifier:**
- Predicts the most frequent class (no purchase)
- Serves as a sanity check to ensure models add value over trivial baselines

### 11.2 Selection Criteria

**Primary metric: PR-AUC (Average Precision)**

PR-AUC is the primary metric because:
- The outcome is imbalanced (~6% positive class)
- PR-AUC focuses on the minority class (purchasers)
- It directly summarizes the precision-recall trade-off across all thresholds
- It is more informative than ROC-AUC for imbalanced problems, as ROC-AUC can appear high even when precision at high recall is poor

**Secondary metrics:**
- ROC-AUC: Probability that a random positive is ranked above a random negative
- Brier score: Mean squared error of predicted probabilities (measures calibration)
- Top-decile lift: Purchase rate in the top decile relative to overall rate
- Top-decile capture: Fraction of purchases captured in the top decile

**Selection process:**
1. Fit both logistic regression and random forest on the training split
2. Evaluate uncalibrated PR-AUC on the validation split
3. Select the model with higher validation PR-AUC
4. Apply sigmoid calibration to the selected model using validation data
5. Select classification threshold by maximizing F1 on calibrated validation probabilities
6. Evaluate the final calibrated model on the held-out test split

---

## 12. Random Forest Selection

### 12.1 Validation Performance

| Model              | Validation PR-AUC | Validation ROC-AUC |
|--------------------|-------------------|-------------------|
| Dummy Classifier   | 0.0404            | 0.5000            |
| Logistic Regression| 0.0980            | 0.7490            |
| Random Forest      | 0.0997            | 0.7524            |

Random Forest achieved a validation PR-AUC of **0.0997**, compared to **0.0980** for logistic regression. The advantage is **narrow** (0.0017), indicating that both models perform similarly on this task.

**Model-selection uncertainty:** The small observed difference does not establish that Random Forest is generally superior to logistic regression. Both models could perform similarly on new data, and the advantage could be due to random variation in the validation set. Random Forest was selected under the predefined procedure (higher validation PR-AUC), but this selection should be viewed as a practical choice rather than evidence of definitive superiority.

### 12.2 Why Random Forest Despite Narrow Margin

Given the narrow performance gap, either model could reasonably be selected. Random Forest was chosen for the following reasons:

- **Non-linear capacity:** Random Forest can capture interactions between features (e.g., specific device-country combinations) without explicit interaction terms.
- **Robustness:** Tree-based models are less sensitive to feature scaling and outliers.
- **No distributional assumptions:** Logistic regression assumes a linear relationship in log-odds, which may not hold for this problem.

However, the narrow margin suggests that a linear model with carefully engineered features could achieve similar performance. Logistic regression coefficients are reported in Section 16 as complementary directional associations.

### 12.3 Random Forest Hyperparameters

The Random Forest uses scikit-learn defaults with the following modifications:
- `n_estimators=200`: Number of trees in the forest
- `class_weight="balanced_subsample"`: Adjusts class weights inversely proportional to class frequencies in each bootstrap sample
- `random_state=42`: Ensures reproducibility
- `n_jobs=-1`: Uses all available CPU cores

No extensive hyperparameter tuning was performed. The focus was on establishing a strong baseline with a standard configuration rather than optimizing marginal performance gains.

---

## 13. Probability Calibration

### 13.1 Why Calibration Is Needed

Raw Random Forest probabilities are not well-calibrated when using `class_weight="balanced_subsample"`. The class weighting pushes predicted probabilities away from the true positive rate to improve recall on the minority class.

**Uncalibrated Brier score:** 0.1778 (test set)  
**Calibrated Brier score:** 0.0457 (test set)

The reduction in Brier score confirms that calibration substantially improves probability reliability.

### 13.2 Calibration Method

**Sigmoid (Platt) calibration** is applied using `CalibratedClassifierCV` with `method="sigmoid"` and `cv=None`.

**Implementation details:**
- The underlying Random Forest is fitted on training data and then frozen using `FrozenEstimator` (available in scikit-learn ≥ 1.4). This prevents the calibration layer from refitting the underlying model.
- The calibration layer is fitted on **validation data only** using `(X_validation, y_validation)`.
- Test data is never used for calibration fitting.
- The configuration uses `CalibratedClassifierCV(method="sigmoid", cv=None)` with `FrozenEstimator`, which is the scikit-learn ≥ 1.4 replacement for the removed `cv='prefit'` parameter.

**Provenance of Brier scores:**
- The uncalibrated Brier score of 0.1778 and calibrated Brier score of 0.0457 are both computed on the **test set**. The calibration was fitted on validation data, but the improvement is evaluated on held-out test data to confirm that calibration generalizes.

**Why sigmoid calibration:**
- Simple and computationally efficient
- Works well when the base model's scores are approximately monotonic with the true probabilities
- Does not require cross-validation folds (cv=None), which simplifies the pipeline

### 13.3 Calibration Evaluation

Calibration is evaluated visually using a calibration curve (reliability diagram) and quantitatively using the Brier score.

**Calibration curve interpretation:** A well-calibrated model lies close to the diagonal, meaning that when the model predicts a 20% purchase probability, approximately 20% of those sessions actually purchase.

The calibration curve shows that the calibrated model is substantially better aligned with the diagonal than the uncalibrated model.

---

## 14. Validation-Based Threshold Selection

### 14.1 Threshold Selection Process

The classification threshold converts continuous probability scores into binary predictions (purchase vs. no purchase). The threshold is selected on the **validation set only** using the following process:

1. Generate calibrated probability predictions on the validation set
2. Evaluate precision, recall, and F1 at 100 candidate thresholds evenly spaced from 0 to 1
3. Select the threshold that maximizes F1 on the validation set

**Selected threshold:** 0.0892

This threshold is then applied unchanged to the test set. No re-optimization is performed on test data.

**Threshold provenance:** The threshold of 0.0892 was selected by maximizing F1 on **calibrated validation probabilities**. Test data was not used in threshold selection. The same threshold is applied to the test set for final evaluation only.

### 14.2 Why F1 for Threshold Selection

F1 is the harmonic mean of precision and recall:

\[
F1 = 2 \times \frac{\text{precision} \times \text{recall}}{\text{precision} + \text{recall}}
\]

F1 balances the trade-off between:
- **Precision:** Minimizing false positives (sessions incorrectly flagged as likely purchasers)
- **Recall:** Minimizing false negatives (purchasing sessions missed by the model)

Using F1 as the selection criterion ensures that the threshold optimizes this balance rather than favoring one metric over the other.

### 14.3 Alternative Threshold Strategies

Other threshold selection strategies could be used depending on operational context:

- **High-precision threshold:** If false positives are costly (e.g., intrusive interventions), select a threshold that achieves a target precision (e.g., 20%).
- **High-recall threshold:** If missing purchasers is costly (e.g., revenue-critical context), select a threshold that achieves a target recall (e.g., 50%).
- **Cost-sensitive threshold:** If the costs of false positives and false negatives can be quantified, select the threshold that minimizes expected cost.

The F1-based threshold is a reasonable default when costs are not explicitly known.

---

## 15. Test-Set Evaluation

All test-set metrics are computed on the held-out test split (January 16–31, 2021) using the calibrated Random Forest with the validation-selected threshold of 0.0892.

### 15.1 Test-Sample Characteristics

- **Sessions:** 13,658
- **Purchases:** 688
- **Purchase prevalence:** 5.04%
- **No-skill PR-AUC baseline:** 0.0504 (equal to prevalence)

### 15.2 Ranking Quality: PR-AUC

**Test PR-AUC:** 0.1402  
**No-skill baseline:** 0.0504

PR-AUC measures the area under the Precision-Recall curve. It summarizes the trade-off between precision and recall across all classification thresholds.

**Interpretation:** A PR-AUC of 0.1402 indicates that the model achieves substantially better precision-recall performance than a random classifier (0.0504 baseline). However, there is considerable room for improvement—this is a challenging prediction task.

**Why PR-AUC over accuracy:**

Accuracy is misleading for imbalanced outcomes. A classifier that always predicts "no purchase" would achieve 94.96% accuracy on the test set (since 94.96% of sessions do not purchase), but it would be useless for identifying purchasers.

PR-AUC focuses on the minority class and directly measures the model's ability to distinguish purchasers from non-purchasers. It is not inflated by the large number of true negatives.

### 15.3 Ranking Quality: ROC-AUC

**Test ROC-AUC:** 0.7876

ROC-AUC measures the probability that a randomly chosen positive example is ranked above a randomly chosen negative example.

**Interpretation:** An ROC-AUC of 0.7876 indicates good ranking quality—the model correctly ranks a random purchaser above a random non-purchaser approximately 79% of the time.

**Why ROC-AUC is secondary:** ROC-AUC can appear high even when precision at high recall is poor for imbalanced targets. PR-AUC is more informative for this problem.

### 15.4 Probability Calibration: Brier Score

**Uncalibrated Brier score:** 0.1778  
**Calibrated Brier score:** 0.0457

The Brier score is the mean squared error between predicted probabilities and binary outcomes:

\[
\text{Brier score} = \frac{1}{N} \sum_{i=1}^{N} (p_i - y_i)^2
\]

where \(p_i\) is the predicted probability and \(y_i\) is the actual outcome (0 or 1).

**Interpretation:** Lower Brier scores indicate better calibration. The substantial reduction from 0.1778 to 0.0457 confirms that sigmoid calibration significantly improves probability reliability.

### 15.5 Thresholded Classification Performance

At the validation-selected threshold of 0.0892:

**Confusion matrix:**

|                     | Predicted: No purchase | Predicted: Purchase |
|---------------------|------------------------|--------------------|
| **Actual: No purchase** | TN = 11,801           | FP = 1,169         |
| **Actual: Purchase**    | FN = 469              | TP = 219           |

**Derived metrics:**

- **Precision:** TP / (TP + FP) = 219 / (219 + 1,169) = 0.1578
- **Recall:** TP / (TP + FN) = 219 / (219 + 469) = 0.3183
- **F1:** 2 × (precision × recall) / (precision + recall) = 0.2110

**Interpretation:**
- Precision of 15.78% means that among sessions flagged as likely purchasers, 15.78% actually purchase. This is 3.12× higher than the overall test purchase rate of 5.04%.
- Recall of 31.83% means that the model correctly identifies 31.83% of all purchasing sessions.
- F1 of 0.2110 balances these two metrics.

**Precision is inherently limited** by the low prevalence of purchases. Even a perfect model would have limited precision if the threshold is set to achieve reasonable recall.

---

## 16. Lift and Purchase Concentration by Score Decile

### 16.1 Decile Analysis

Sessions in the test set are divided into ten equal-sized deciles based on their predicted purchase probability. Decile 1 contains the highest-scoring 10% of sessions; decile 10 contains the lowest-scoring 10%.

| Decile | Sessions | Purchases | Purchase Rate | Lift vs. Overall |
|--------|----------|-----------|---------------|-------------------|
| 1 (highest) | 1,366 | 215 | 15.74% | 3.12× |
| 2 | 1,366 | 157 | 11.49% | 2.28× |
| 3 | 1,366 | 106 | 7.76% | 1.54× |
| 4 | 1,365 | 87 | 6.37% | 1.27× |
| 5 | 1,366 | 56 | 4.10% | 0.81× |
| 6 | 1,366 | 36 | 2.64% | 0.52× |
| 7 | 1,365 | 14 | 1.03% | 0.20× |
| 8 | 1,366 | 7 | 0.51% | 0.10× |
| 9 | 1,366 | 10 | 0.73% | 0.15× |
| 10 (lowest) | 1,366 | 0 | 0.00% | 0.00× |
| **Overall** | **13,658** | **688** | **5.04%** | — |

### 16.2 Lift Calculation

Lift is the ratio of the purchase rate in a decile to the overall purchase rate:

\[
\text{Lift} = \frac{\text{Purchase rate in decile}}{\text{Overall purchase rate}}
\]

For the top decile:

\[
\text{Lift}_{\text{decile 1}} = \frac{0.1574}{0.0504} = 3.12
\]

**Interpretation:** Sessions in the top decile convert at 3.12 times the average rate. This indicates strong ranking quality—the model successfully concentrates purchases in the highest-scoring sessions.

### 16.3 Purchase Capture

Purchase capture is the fraction of all purchases that fall within a given decile:

\[
\text{Purchase capture} = \frac{\text{Purchases in decile}}{\text{Total purchases}}
\]

For the top decile:

\[
\text{Purchase capture}_{\text{decile 1}} = \frac{215}{688} = 0.3125 = 31.3\%
\]

**Interpretation:** By targeting only the top 10% of sessions, one would reach 31.3% of all purchasers. This demonstrates the operational value of the model for capacity-constrained targeting.

### 16.4 Marginal Returns

The decile analysis shows diminishing marginal returns as targeting expands into lower-scored deciles:

- **Decile 1:** 31.3% of purchases captured, 3.12× lift
- **Deciles 1–2:** 51.6% of purchases captured, 2.70× average lift
- **Deciles 1–3:** 67.0% of purchases captured, 2.31× average lift
- **Deciles 1–5:** 84.6% of purchases captured, 1.69× average lift

This pattern informs the economic decision perspective discussed in Section 18: if targeting capacity is limited, focusing on the top deciles maximizes the purchase rate per targeted session.

---

## 17. Interpretation and Feature Associations

### 17.1 Logistic Regression Coefficients

**Important caveat:** These coefficients are from the **logistic regression model**, not the selected Random Forest. They represent **associations** from a benchmark model and do not explain individual Random Forest predictions. They are complementary directional information, not the driving factors of the selected model.

Although Random Forest was selected by validation PR-AUC, logistic regression coefficients provide interpretable directional associations between features and purchase probability.

**Important caveats:**
- They represent **associations**, not causal effects.
- The data is observational; coefficient magnitude does not imply causal importance.
- Coefficients are based on **scaled and encoded features**—they are not directly comparable to raw feature values.

**Top-20 features by absolute coefficient magnitude:**

| Feature | Coefficient | Direction |
|---------|-------------|-----------|
| `first_item_category_Women's` | +1.36 | Higher purchase propensity |
| `first_item_category_Home/Campus Collection/` | +1.05 | Higher purchase propensity |
| `first_item_category_Drinkware` | +0.99 | Higher purchase propensity |
| `first_item_category_Home/Apparel/Socks/` | +0.98 | Higher purchase propensity |
| `first_item_name_google incognito flap pack` | +0.96 | Higher purchase propensity |
| `first_item_category_Home/Stationery/Writing/` | +0.94 | Higher purchase propensity |
| `first_item_name_supernatural paper backpack` | -0.92 | Lower purchase propensity |
| `first_item_name_google cambridge campus zip hoodie` | -0.97 | Lower purchase propensity |
| `first_item_category_Home/Stationery/` | -1.00 | Lower purchase propensity |
| `country_Croatia` | -1.01 | Lower purchase propensity |
| `first_item_name_google pocket tee grey` | -1.06 | Lower purchase propensity |
| `country_Romania` | -1.07 | Lower purchase propensity |
| `first_item_category_Eco-Friendly` | -1.28 | Lower purchase propensity |
| `country_Morocco` | -1.34 | Lower purchase propensity |
| `country_Norway` | -1.57 | Lower purchase propensity |
| `first_item_name_google tee blue` | -1.74 | Lower purchase propensity |
| `first_item_category_Accessories/` | -1.88 | Lower purchase propensity |
| `first_item_name_(unknown)` | -1.99 | Lower purchase propensity |
| `first_item_category_Backpacks/` | -2.06 | Lower purchase propensity |
| `first_item_name_google mural sticker sheet` | -2.13 | Lower purchase propensity |

### 17.2 Interpreting Coefficients

**Log-odds interpretation:** Logistic regression models the log-odds of purchase as a linear function of features:

\[
\log\left(\frac{P(\text{purchase})}{1 - P(\text{purchase})}\right) = \beta_0 + \beta_1 x_1 + \beta_2 x_2 + \dots
\]

A coefficient of +1.36 for `first_item_category_Women's` means that, holding all other features constant, viewing a women's apparel item increases the log-odds of purchase by 1.36 compared to the reference category.

**Odds ratio interpretation:** Exponentiating the coefficient gives the odds ratio:

\[
\text{Odds ratio} = e^{\beta}
\]

For `first_item_category_Women's`: \(e^{1.36} = 3.90\). This means the odds of purchase are approximately 3.9× higher for sessions viewing women's apparel compared to the reference category.

**Reference categories:** The reference category for each one-hot encoded feature is the category that is omitted from the encoding (typically the most frequent category or a designated baseline). Coefficients are interpreted relative to this reference.

**Regularization:** L2 regularization shrinks coefficients toward zero to prevent overfitting. This means coefficients may be slightly attenuated compared to an unregularized model.

### 17.3 Feature Scaling and Encoding

**Numerical features:** Standardized to zero mean and unit variance before model fitting. Coefficients represent the effect of a one-standard-deviation increase in the scaled feature.

**Categorical features:** One-hot encoded with a minimum frequency threshold of 50. Categories appearing fewer than 50 times in the training set are grouped into an "infrequent" bucket.

**Cyclic encoding:** Hour-of-day and day-of-week are encoded as sine/cosine components, which are then standardized. The coefficients for these components are difficult to interpret directly—directional patterns are better understood through visualization.

### 17.4 Random Forest Feature Importance

Random Forest provides feature importance measures (e.g., mean decrease in impurity), but these are not reported here because:

- They are less interpretable than logistic regression coefficients
- They can be biased toward high-cardinality features
- They do not provide directional information (positive vs. negative association)

Logistic regression coefficients serve as a more interpretable complement to the Random Forest's superior ranking performance.

---

## 18. Economic Decision Perspective

### 18.1 Scarcity and Opportunity Cost

The model is most valuable when there is a **binding capacity constraint**—when we cannot intervene on all sessions. Common constraints include:

- **Limited customer-service capacity:** Only a certain number of agents can engage visitors via live chat
- **Limited promotional budget:** Only a certain number of discount offers can be distributed
- **Limited analytical capacity:** Only a certain number of sessions can be qualitatively reviewed

Under scarcity, the opportunity cost of intervening on a low-propensity session is the forgone opportunity to intervene on a high-propensity session instead.

### 18.2 Ranking Under a Capacity Constraint

The model's primary operational value is **ranking** sessions by purchase propensity. If we can intervene on only K sessions, we should select the K sessions with the highest predicted scores.

**Example:** If we can engage 1,000 sessions via live chat, the model would recommend selecting the 1,000 highest-scoring sessions. Based on test-set decile analysis, this would capture approximately 31.3% of purchases (if K = 1,366, the top decile).

### 18.3 Marginal Returns

The decile analysis (Section 16) shows that marginal returns diminish as we expand targeting into lower-scored deciles:

- **Top decile:** 3.12× lift, 31.3% of purchases
- **Second decile:** 2.28× lift, additional 22.8% of purchases in that decile
- **Third decile:** 1.54× lift, additional 15.4% of purchases in that decile

This pattern informs the optimal targeting scope under capacity constraints. If capacity is very limited, focus on the top decile. If capacity is larger, expand into lower deciles, but recognize that the purchase rate per targeted session will decline.

### 18.4 Threshold Selection Based on Costs

The classification threshold can be selected based on the **economic trade-off** between:

- **Cost of intervention (C):** The cost of engaging a session (e.g., agent time, discount value)
- **Benefit of successful intervention (B):** The expected revenue or profit from a converted session

**Expected value framework:** For a session with predicted purchase probability \(p\):

\[
\text{Expected net benefit} = p \times B - C
\]

Intervention is worthwhile when \(p \times B > C\), or equivalently when \(p > C / B\).

**Threshold implication:** If intervention costs $10 and the expected benefit from a conversion is $100, the break-even threshold is \(p = 10 / 100 = 0.10\). Sessions with predicted probability above 0.10 should be targeted.

**Current limitation:** This project does not include intervention costs, customer lifetime value, or incremental treatment-effect estimates. Therefore, the F1-based threshold (0.0892) is a reasonable default but not economically optimized. Profitability analysis requires additional information that is not available in the current dataset.

### 18.5 Propensity vs. Incremental Response

**Important distinction:** The model predicts **baseline purchase propensity**—the probability that a session will purchase in the absence of intervention. It does **not** predict **incremental treatment response**—the increase in purchase probability caused by an intervention.

**Why this matters:**
- High-propensity sessions may purchase even without intervention (low incremental response). Targeting them may waste resources if they would convert anyway.
- Low-propensity sessions may be most responsive to intervention (high incremental response). Focusing only on high-propensity sessions may miss opportunities to persuade uncertain visitors.
- Targeting based solely on propensity may not maximize incremental revenue or profit.

**Uplift modeling:** To estimate incremental treatment response, we would need:
- Randomized treatment assignments (A/B test data)
- Features from both treated and control groups
- A model trained on the difference in outcomes between treatment and control

**Current scope:** This project does not contain treatment assignments or causal estimates. The model identifies sessions that are *likely to purchase*, not sessions that are *likely to respond to intervention*. The model cannot identify "persuadable" customers or optimize intervention profitability without additional experimental data and cost information.

### 18.6 Causal Scope

**Associations vs. causality:** The model identifies statistical associations between early-session signals and purchase outcomes. It does not establish that any feature *causes* higher conversion.

**Example:** The model shows that sessions viewing "Women's" apparel have higher purchase propensity. This does not mean that showing women's apparel to more visitors would increase conversions—it may simply reflect that visitors interested in women's apparel are more likely to purchase overall.

**Controlled experiments:** To establish causality, randomized experiments are required. The model can inform experiment design (e.g., which segments to test), but model scores alone should not be used to make causal claims or guide interventions without experimental validation.

---

## 19. Limitations

### 19.1 Data Limitations

**Historical and observational:** The data is historical and observational. The model learns patterns from past behavior, which may not generalize to future periods or different contexts.

**Public GA4 data is obfuscated:** The dataset is a public sample with obfuscated user identifiers and may not represent the full complexity of production GA4 data.

**Limited time period:** The data covers only November 2020 through January 2021 (three months). Seasonal patterns (e.g., holiday shopping) may limit generalization to other time periods.

**Conversion drift:** Purchase rates declined across the chronological splits (6.71% → 4.04% → 5.04%), indicating temporal drift. Model performance may degrade outside the analyzed period.

### 19.2 Attribution Limitations

**First-user attribution:** `acquisition_source` and `acquisition_medium` reflect first-user acquisition, not session-level attribution. Interpreting them as the source driving a specific session is incorrect.

**No session-level campaign data:** The dataset does not include session-level campaign parameters (e.g., UTM tags for the current session). Therefore, we cannot model session-level acquisition effects.

### 19.3 Tracking Limitations

**`add_to_cart` tracking unreliable:** During parts of the period (November 1–15 and November 21–24), `add_to_cart` tracking was unreliable or unavailable. This limits the analysis of the cart-to-checkout transition.

**Potential untracked events:** Other events (e.g., video views, file downloads) may be relevant to purchase behavior but are not included in the feature set.

### 19.4 Model Limitations

**Feature constraints:** Features are limited to information available at the first product view. Signals that become available later in the session (e.g., time spent on product page, specific items added to cart) are excluded.

**No treatment information:** The model does not incorporate any information about interventions, promotions, or experimental treatments. It predicts baseline propensity, not incremental response.

**No customer value:** The model predicts purchase occurrence, not purchase value or customer lifetime value. High-propensity sessions may result in low-value purchases.

**Static model:** The model is not designed to update continuously. In production, it would require periodic retraining to account for concept drift.

### 19.5 Generalization Limitations

**Single merchant:** The model is trained on data from a single merchant (Google Merchandise Store). Performance may differ for other e-commerce contexts.

**Single geography:** The dataset includes global traffic, but the majority of sessions may come from specific regions. Geographic patterns may not generalize.

**Device-specific patterns:** Device behavior may evolve over time (e.g., mobile vs. desktop conversion rates). The model may not capture future shifts.

### 19.6 Interpretation Limitations

**Associations not causality:** As emphasized throughout, model associations do not establish causal effects. Controlled experiments are required before acting on model scores.

**Coefficient interpretation limits:** Logistic regression coefficients are affected by feature scaling, encoding choices, and regularization. They should be interpreted as directional associations, not precise effect sizes.

**Feature importance ambiguity:** Random Forest feature importance measures are not reported due to interpretability limitations. Logistic regression coefficients provide more interpretable but model-specific associations.

---

## 20. Deployment Considerations and Next Experiments

### 20.1 Deployment Considerations

**Monitoring required:** Before operational use, the model would require:
- **Calibration monitoring:** Track whether predicted probabilities remain calibrated over time
- **Performance monitoring:** Track PR-AUC, lift, and capture rate on new data
- **Drift detection:** Monitor feature distributions and purchase rates for drift

**Feature pipeline:** The feature engineering SQL (`sql/09_model_features.sql`) would need to be productionized as a scheduled query or streaming pipeline to generate features for scoring.

**Model serialization:** The current notebook does not serialize the fitted model. For deployment, the model pipeline would need to be saved (e.g., using `joblib` or `pickle`) and loaded in a scoring service.

**Latency requirements:** If real-time scoring is required (e.g., scoring at the moment of product view), the feature pipeline and model inference must meet latency constraints. Batch scoring (e.g., scoring sessions every few minutes) may be more practical.

**Privacy and ethics:** The model uses session-level features that do not include personally identifiable information in this obfuscated dataset. In production, ensure compliance with privacy regulations (e.g., GDPR, CCPA) and ethical guidelines for targeting.

### 20.2 Next Experiments

**Causal experiments:** The most important next step is to conduct randomized experiments to estimate incremental treatment effects:

- **Live chat experiment:** Randomly assign high-propensity vs. low-propensity sessions to live chat offers and measure incremental conversion.
- **Discount experiment:** Randomly assign discount offers to sessions at different propensity levels and measure incremental revenue.
- **Uplift modeling:** If experimental data is available, train an uplift model to predict incremental response rather than baseline propensity.

**Feature expansion:** Additional features could improve model performance:

- **Session-level attribution:** If session-level campaign data becomes available, incorporate it into the feature set.
- **Post-view signals (for uplift modeling):** For experiments, features measured after the prediction moment (e.g., time on page, scroll depth) may be useful for predicting incremental response.
- **Cross-session features:** User-level features (e.g., past purchase history, session count) could improve predictions if user identification is reliable.

**Alternative model architectures:**
- **Gradient boosting:** Models like XGBoost or LightGBM may achieve better performance than Random Forest.
- **Neural networks:** Deep learning models could capture complex patterns but require more data and tuning.
- **Ensemble methods:** Combining multiple models (e.g., Random Forest + logistic regression) may improve robustness.

**Threshold optimization:** If intervention costs and benefits can be quantified, optimize the threshold based on expected net value rather than F1.

**Time-series modeling:** Incorporate temporal features (e.g., day-of-year, holiday indicators) to better capture seasonal patterns.

**Multi-merchant validation:** Test the model on data from other e-commerce merchants to assess generalization.

---

## 21. Reproducibility and Source Files

### 21.1 Reproducibility

**Random seed:** All stochastic operations use a fixed random seed (42) to ensure reproducibility.

**Deterministic preprocessing:** Feature engineering transformations are deterministic and do not involve fitting on data statistics.

**Versioned dependencies:** The `requirements.txt` file specifies exact package versions used in the analysis.

**Artifact preservation:** All evaluation metrics, decile tables, coefficient tables, and figures are committed to the repository in `data/processed/demo/` and `images/`.

### 21.2 Source Files

**Notebook:** `notebooks/03_purchase_prediction.ipynb`
- Model training, evaluation, and artifact generation
- All numerical results and figures originate from this notebook

**Feature SQL:** `sql/09_model_features.sql`
- Leakage-safe feature extraction from GA4 export
- Enforces temporal boundary at first `view_item`

**Feature validation SQL:** `sql/13_model_feature_validation.sql`
- Verifies that features respect the temporal boundary
- Checks for post-view event leakage

**Data dictionary:** `docs/data_dictionary.md`
- Documents all model features and their sources
- Specifies prediction-time availability

**Metric definitions:** `docs/metric_definitions.md`
- Defines all evaluation metrics used in the report
- Specifies formulas and interpretation

**Committed artifacts:**
- `data/processed/demo/model_metrics.json` — All evaluation metrics
- `data/processed/demo/model_test_deciles.csv` — Decile analysis table
- `data/processed/demo/model_validation_comparison.csv` — Validation model comparison
- `data/processed/demo/model_logistic_coefficients.csv` — Logistic regression coefficients
- `data/processed/demo/model_pr_curves.csv` — Precision-recall curve data
- `data/processed/demo/model_calibration_curves.csv` — Calibration curve data

**Figures:**
- `images/model_decile_lift.png` — Purchase rate by decile
- `images/model_precision_recall.png` — Precision-recall curves
- `images/model_calibration.png` — Calibration curves

### 21.3 Dashboard

**Streamlit application:** `dashboard/pages/04_purchase_propensity.py`
- Displays pre-computed model evaluation results
- Does not perform live predictions or access BigQuery
- Uses committed artifacts from `data/processed/demo/`

**Dashboard verification:** The dashboard runs without BigQuery credentials because it loads only pre-computed CSV and JSON artifacts. No live database queries are performed.

### 21.4 Running the Analysis

To reproduce the model training and evaluation:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the notebook
jupyter notebook notebooks/03_purchase_prediction.ipynb
```

The notebook reads the feature extract from `data/processed/demo/model_features.csv.gz`, which is already committed to the repository. To regenerate the feature extract from BigQuery, run the SQL queries in `sql/09_model_features.sql`.

---

## Appendix: Evaluation Stage Mapping

| Stage | Split | Purpose | Metrics Used |
|-------|-------|---------|---------------|
| Model fitting | Train | Fit logistic regression and random forest pipelines | — |
| Model selection | Validation | Compare models by PR-AUC, select Random Forest | Validation PR-AUC: LR 0.0980, RF 0.0997 |
| Calibration fitting | Validation | Fit sigmoid calibration layer on validation data | Brier score reduction: 0.1778 → 0.0457 |
| Threshold selection | Validation | Select threshold by maximizing F1 on calibrated probabilities | Selected threshold: 0.0892 |
| Final evaluation | Test | One-time evaluation of calibrated model with locked threshold | Test PR-AUC: 0.1402, test lift: 3.12×, test capture: 31.3% |

**Key principle:** Test data is never used for model fitting, calibration, or threshold selection. All decisions are made on training or validation data only.
