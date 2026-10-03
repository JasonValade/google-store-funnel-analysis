# Technical Methodology: Analysis Journey & Decisions

This document walks through the analytical journey, technical decisions, and rationale behind the Google Store Funnel Analysis.

---

## Table of Contents

1. [Data Understanding & Exploration](#1-data-understanding--exploration)
2. [Funnel Definition & Construction](#2-funnel-definition--construction)
3. [Segmentation Analysis](#3-segmentation-analysis)
4. [Tracking Health Monitoring](#4-tracking-health-monitoring)
5. [Feature Engineering for Prediction](#5-feature-engineering-for-prediction)
6. [Model Development & Evaluation](#6-model-development--evaluation)
7. [Dashboard Implementation](#7-dashboard-implementation)

---

## 1. Data Understanding & Exploration

### Initial Data Assessment

**Source:** `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

**Challenge:** The dataset spans multiple tables (`events_202011*`, `events_202012*`, `events_202101*`) requiring `_TABLE_SUFFIX` for cost-efficient querying.

**Decision:** Used BigQuery Standard SQL with `_TABLE_SUFFIX BETWEEN '20201101' AND '20210131'` to query the relevant date range without scanning unnecessary tables.

### Data Quality Checks

**File:** `sql/02_data_quality.sql`

**Findings:**
- `add_to_cart` events were unreliable November 1-15 (counts near zero despite traffic)
- Complete outage November 21-24 (zero `add_to_cart` events)
- Item identifiers inconsistent across event types (same product had different IDs)

**Decisions:**
1. Restricted funnel analysis to dates with reliable `add_to_cart` tracking (Nov 16-20, Nov 25-Jan 31)
2. Normalized product names instead of using item IDs for product-level analysis
3. Documented tracking limitations prominently in all outputs

### Event Schema Inspection

**File:** `sql/00_schema_inspection.sql`

**Key fields identified:**
- `event_name` - Event type (page_view, view_item, add_to_cart, etc.)
- `event_timestamp` - Microsecond-precision timestamp
- `user_pseudo_id` - Anonymous user identifier
- `ga_session_id` - Session identifier
- `event_params` - Nested array of event-specific parameters
- `items` - Nested array of item information for e-commerce events

**Challenge:** GA4 uses nested fields (`event_params`, `items`) requiring UNNEST for analysis.

**Solution:** Used `UNNEST(event_params)` to extract key parameters like page location, item names, and transaction IDs.

---

## 2. Funnel Definition & Construction

### Funnel Stage Definition

**Business Question:** Where do customers abandon the purchase journey?

**Initial Approach:** Simple event counting
- Count each event type (view_item, add_to_cart, begin_checkout, purchase)
- Calculate conversion rates between stages

**Problem:** This doesn't account for:
- Sessions with multiple events of the same type
- Sessions that skip stages (purchase without add_to_cart)
- Temporal ordering (did purchase happen before view?)

**Refined Approach:** Session-level ordered funnel

**Files:** `sql/03_user_funnel.sql`, `sql/04_session_funnel.sql`, `sql/05_ordered_session_funnel.sql`

**Key Decisions:**

1. **Session Key:** `user_pseudo_id || '_' || ga_session_id`
   - Rationale: GA4 sessions are scoped to users, but user_pseudo_id alone doesn't distinguish multiple sessions from the same user

2. **Timestamp Ordering:** Required events to occur in strict chronological order
   - `view_item` must be first
   - `add_to_cart` must be after `view_item`
   - `begin_checkout` must be after `add_to_cart`
   - `purchase` must be after `begin_checkout`

3. **Funnel Scope:** Only sessions with reliable `add_to_cart` tracking
   - Rationale: Cart stage is unreliable in early November; including it would distort funnel metrics

**Result:** 77,020 sessions completed the ordered funnel from view_item to purchase, with 6.05% overall conversion.

### Alternative Funnel Definitions

**Model Population Definition:** Broader definition for ML modeling
- Requirement: Purchase must occur after first `view_item`
- No requirement for intermediate stages
- Rationale: Model should learn from all purchasing sessions, not just those following the ideal path

**Difference:** 27 additional sessions (4,688 vs. 4,661) purchased without completing all funnel stages.

---

## 3. Segmentation Analysis

### Device Segmentation

**File:** `sql/06_device_analysis.sql`

**Approach:** Join funnel sessions with device category from the first `view_item` event.

**Finding:** Mobile (6.26%) slightly outperformed desktop (5.91%).

**Statistical Test:** Chi-square test of independence
- Result: Borderline statistically significant (p ≈ 0.06)
- Interpretation: Difference exists but may not be practically significant

**Decision:** Reported both raw rates and statistical context to avoid overinterpretation.

### Traffic Source Segmentation

**File:** `sql/07_traffic_source_analysis.sql`

**Challenge:** GA4 provides `first_user_source` and `first_user_medium` - these describe the user's *first* acquisition, not the source of the current session.

**Decision:** Clearly documented this limitation in all outputs. The analysis shows first-touch attribution, not session-level attribution.

**Finding:** Direct traffic (5.92%) > Google organic (5.08%) > Google CPC (4.74%).

**Insight:** Self-referrals may be inflating direct traffic; recommend attribution audit.

### Product Segmentation

**File:** `sql/08_product_analysis.sql`

**Challenge:** Item IDs inconsistent across event types (same product had different IDs in view_item vs. purchase events).

**Solution:** Normalized product names by:
1. Extracting `item_name` from `items` array
2. Lowercasing and removing special characters
3. Using normalized names as the product identifier

**Finding:** Several high-traffic products had 1-2% conversion rates.

**Caveat:** These could be:
- Merchandising issues (products customers don't want)
- Inventory issues (out of stock but still browsable)
- Tracking issues (events not firing)
- UX issues (confusing product pages)

**Recommendation:** Audit before taking action.

---

## 4. Tracking Health Monitoring

### Problem Identification

During initial exploration, discovered `add_to_cart` events dropped to zero on specific dates despite continued page views.

**Question:** Is this a tracking failure or a legitimate traffic/behavior change?

### Monitoring Approach

**File:** `sql/12_tracking_health_monitor.sql`

**Signal Design:**

1. **Rolling 7-day baseline** - Calculate expected event counts based on recent history
2. **Event-volume ratio** - Compare actual event count to baseline
3. **Z-score** - Statistical measure of deviation from expected
4. **Page-view context** - Compare event count to page view count to detect event-specific issues
5. **Traffic-adjusted event ratio** - Normalize by overall session volume

**Thresholds:**
- Event-volume ratio < 0.5 → Potential tracking failure
- Page-view ratio < 0.5 → Event-specific issue (not general traffic decline)
- Z-score > 3 → Statistically significant deviation

**Validation:** Manually confirmed four outage dates (Nov 21-24) by checking event counts.

**Result:** Monitor correctly identified all four outages and distinguished them from general traffic declines.

**Limitation:** Prototype requires manual threshold tuning; production system would need adaptive thresholds.

---

## 5. Feature Engineering for Prediction

### Problem Statement

**Question:** Can early-session behavior predict whether a purchase will occur later in the session?

**Constraint:** Use only information available at the time of the first `view_item` event to prevent leakage.

### Feature Categories

**File:** `sql/09_model_features.sql`

#### 1. Temporal Features
- `seconds_to_first_view` - Time from session start to first product view
- `hour_sin`, `hour_cos` - Cyclical encoding of hour of day
- `dow_sin`, `dow_cos` - Cyclical encoding of day of week

**Rationale:** Purchase behavior varies by time (e.g., evening shopping, weekend purchases). Cyclical encoding preserves temporal proximity (23:00 is close to 00:00).

#### 2. Pre-View Engagement
- `page_views_before_first_view`
- `scroll_events_before_first_view`
- `search_events_before_first_view`
- `promotion_views_before_first_view`
- `engagement_events_before_first_view`

**Rationale:** Users who browse, search, or engage before viewing products may be in different purchase mindsets.

**Transformation:** Applied `log1p` transformation to handle skewed distributions.

#### 3. First Item Information
- `first_item_name` - One-hot encoded product name
- `first_item_category` - One-hot encoded category
- `first_item_price` - Log-transformed price

**Rationale:** The first product viewed may indicate user intent (e.g., browsing expensive items vs. clearance items).

**Limitation:** Only captures first view; users may view multiple items.

#### 4. User Characteristics
- `is_new_visitor` - First-time user flag
- `country` - One-hot encoded country
- `device_category` - One-hot encoded device type
- `acquisition_source` - First-touch acquisition source
- `acquisition_medium` - First-touch acquisition medium

**Rationale:** User context influences purchase likelihood.

**Caveat:** Acquisition fields describe first touch, not session-level attribution.

#### 5. Session Characteristics
- `long_pre_view_session` - Flag for sessions with > 30 seconds before first view
- `item_metadata_missing` - Flag for sessions with missing item information

**Rationale:** Long browsing before viewing may indicate research vs. purchase intent.

### Leakage Prevention

**Critical Design Decision:** Strict temporal split

- Features only use data from events **before** or **at** the first `view_item`
- Target (purchase) only considers purchases **after** the first `view_item`
- Feature extraction in SQL ensures this separation at the data level

**Validation:** `sql/13_model_feature_validation.sql` checks for:
- No future information in features
- Consistent timestamps
- No data leakage between train/validation/test splits

### Feature Validation

**File:** `sql/13_model_feature_validation.sql`

**Checks performed:**
1. Timestamp ordering - Ensure feature times ≤ purchase times
2. Missing value analysis - Identify features with high missingness
3. Distribution checks - Identify extreme outliers
4. Correlation analysis - Detect highly correlated features

**Decisions:**
- Dropped features with > 50% missing values
- Applied log transformation to skewed numerical features
- One-hot encoded categorical features with < 20 levels
- Grouped rare categories into "Other"

---

## 6. Model Development & Evaluation

### Problem Framing

**Task:** Binary classification - predict whether a purchase occurs in a session

**Label:** `purchased_later_in_session` (1 if purchase after first view_item, 0 otherwise)

**Imbalance:** 6.09% of sessions result in purchase (imbalanced classification problem)

### Train/Validation/Test Split

**Approach:** Chronological split to prevent leakage

- Train: Nov 16 - Dec 15, 2020
- Validation: Dec 16 - Dec 31, 2020
- Test: Jan 1 - Jan 31, 2021

**Rationale:** Time-based split simulates real-world deployment where model predicts future behavior.

**Drift:** Test set prevalence (5.04%) lower than train (6.09%) due to post-holiday decline.

### Model Selection

**Models evaluated:**
1. **DummyClassifier** - Stratified random guessing (baseline)
2. **Logistic Regression** - Interpretable linear model
3. **Random Forest** - Non-linear ensemble

**Evaluation metric:** **PR-AUC** (Precision-Recall AUC)

**Rationale for PR-AUC:**
- Appropriate for imbalanced classification
- Focuses on positive class (purchases)
- More informative than ROC-AUC when class imbalance is high

**Results:**
- Dummy: PR-AUC = 0.0504 (no-skill baseline)
- Logistic Regression: PR-AUC = 0.1285
- Random Forest: PR-AUC = 0.1402

**Decision:** Selected Random Forest for final model (best performance, still interpretable via feature importance).

### Feature Importance

**Logistic Regression:** Coefficients show direction and magnitude of association
- Positive coefficients → higher purchase probability
- Negative coefficients → lower purchase probability
- **Caveat:** Associations are not causal effects

**Random Forest:** Feature importance based on impurity reduction
- Identifies most predictive features
- Less interpretable than logistic regression

**Top features:** Item category, device type, session engagement metrics.

### Calibration

**Problem:** Model outputs probabilities, but are they well-calibrated?

**Approach:** Sigmoid calibration (Platt scaling)

**Method:**
1. Fit calibration on validation set only (not test)
2. Apply calibrated model to test set
3. Compare predicted vs. observed purchase rates

**Result:** Calibration improved but not perfect; model slightly overestimates low-probability cases.

**Brier score:** 0.0457 (lower is better; perfect classifier = 0, random = 0.06)

### Decile Analysis

**Approach:** Rank sessions by predicted probability, divide into 10 deciles

**Finding:** Top decile (highest predicted risk) has 3.12× lift over average

- Top decile purchase rate: 15.73%
- Overall test rate: 5.04%
- Captures 31.3% of all purchases from just 10% of sessions

**Business application:** Target high-decile sessions for interventions (promotions, support).

### Threshold Selection

**Approach:** Choose probability threshold on validation set to maximize business metric

**Metrics considered:**
- Precision (minimize false positives)
- Recall (capture more purchases)
- F1-score (balance precision and recall)

**Decision:** No single threshold recommended; threshold should be chosen based on business context:
- High precision (e.g., 0.8) → Targeted campaigns where false positives are costly
- High recall (e.g., 0.8) → Broad outreach where missing purchases is costly

---

## 7. Dashboard Implementation

### Design Philosophy

**Goal:** Share insights without requiring BigQuery credentials or live data access.

**Solution:** Pre-compute analytical artifacts and ship them with the application.

**Artifacts:**
- CSV files for tabular data (device funnel, weekly conversion, tracking alerts)
- JSON for model metrics
- Compressed CSV for large feature file (77K rows)

### Architecture

**File:** `dashboard/app.py`

**Multi-page design:**
1. Executive Overview - High-level metrics and key findings
2. Funnel & Conversion Trends - Time-series and funnel visualization
3. Device & Product Insights - Segment-level analysis
4. Tracking Health - Alert timeline and monitoring signals
5. Purchase Propensity - Model performance and decile analysis
6. Methodology - Technical approach and limitations

**Data loading:** `dashboard/utils/data_loader.py`
- Cached loaders for small CSVs
- Direct loaders for model artifacts (no caching to reflect file changes)
- Error handling for missing artifacts

**Chart building:** `dashboard/utils/charts.py`
- Reusable Plotly chart functions
- Consistent theming (Okabe-Ito color palette for colorblind accessibility)
- Native Streamlit components where possible

### Styling

**Approach:** Layer custom CSS on top of Streamlit's dark theme

**Goals:**
- Professional appearance
- Readable typography
- Consistent spacing
- Accessible colors

**Implementation:** `inject_global_styles()` in `data_loader.py`
- Design tokens for colors, spacing, border radius
- Component-specific styling (metrics, tabs, alerts)
- Focus outlines for keyboard navigation

### Deployment

**Streamlit Cloud:** Deployed as public app at `app-store-funnel-analysis.streamlit.app`

**Configuration:** `.streamlit/config.toml`
- Dark theme enabled
- Wide layout for data visualization
- Expanded sidebar for navigation

**Security:**
- No credentials required
- Pre-computed artifacts only
- No user authentication needed (public demo)

---

## Key Learnings & Retrospective

### What Worked Well

1. **Strict temporal separation** in feature engineering prevented leakage
2. **Manual tracking validation** confirmed monitoring signals were accurate
3. **Multi-page dashboard** allowed both business and technical audiences
4. **Pre-computed artifacts** made deployment simple and secure

### Challenges Faced

1. **GA4 data complexity** - Nested fields required significant SQL engineering
2. **Tracking reliability** - Had to exclude early November from funnel analysis
3. **Item ID inconsistency** - Required product name normalization
4. **Class imbalance** - Required careful metric selection (PR-AUC vs ROC-AUC)

### What I'd Do Differently

1. **Earlier A/B test planning** - Would design experiments alongside analysis
2. **Real-time monitoring** - Would implement automated alerts sooner
3. **Feature documentation** - Would create data dictionary earlier
4. **Model monitoring plan** - Would define drift detection criteria upfront

### Recommendations for Future Work

1. **Live integration** - Connect to production GA4 for real-time insights
2. **Experimentation platform** - Integrate with A/B testing framework
3. **Model monitoring** - Implement drift detection and retraining pipeline
4. **Personalization** - Extend propensity model to recommendation engine
5. **Attribution improvement** - Implement session-level attribution tracking

---

## Conclusion

This analysis demonstrates a complete data science workflow: from raw event data to actionable business insights, with technical rigor in feature engineering, model development, and evaluation. The approach prioritizes preventing leakage, validating assumptions, and communicating findings clearly to both technical and business audiences.
