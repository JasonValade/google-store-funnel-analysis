# Google Merchandise Store Funnel Analysis

An end-to-end analytics portfolio project that turns 4.3 million Google Analytics 4 events into funnel insights, tracking-health alerts, and a purchase-propensity model.

[**View the live Streamlit dashboard**](https://app-store-funnel-analysis.streamlit.app/) · [Metric definitions](docs/metric_definitions.md) · [Data dictionary](docs/data_dictionary.md)

![Primary ordered conversion funnel](images/primary_conversion_funnel.png)

## Project impact

- Analyzed **4,295,584 events** across **360,129 sessions** from the public Google Merchandise Store GA4 export.
- Built a timestamp-validated funnel covering **77,020 product-view sessions** and identified the largest loss between product view and checkout.
- Detected all four manually confirmed `add_to_cart` outage dates with a traffic-adjusted tracking-health monitor.
- Developed a leakage-safe purchase-propensity model with **0.1402 test PR-AUC**, versus a **0.0504 no-skill baseline**.
- Ranked the highest-risk scoring decile at **3.13× lift**, capturing **31.2% of purchases**.
- Shipped a six-page Streamlit dashboard powered by committed, pre-computed artifacts—no credentials or live database required.

## Business question

Where do customers abandon the purchase journey, which segments and products underperform, and can early-session behavior identify visitors who are more likely to purchase?

The project addresses this through four connected workstreams:

1. Ordered session-funnel analysis
2. Device, acquisition, and product segmentation
3. GA4 tracking-health monitoring
4. Session-level purchase-propensity modeling

## Key findings

### Conversion funnel

| Stage | Sessions | Stage conversion |
|---|---:|---:|
| Product view | 77,020 | — |
| Begin checkout | 10,770 | 13.98% from product view |
| Purchase | 4,661 | 43.28% from checkout |
| **Overall** | — | **6.05%** |

The largest opportunity is the product-view-to-checkout transition: **86% of product-view sessions did not begin checkout**.

The clean four-stage cart funnel was limited to dates with reliable `add_to_cart` tracking. During that period, only **34.94% of cart sessions progressed to checkout**.

### Conversion trends and segments

- Weekly purchase conversion peaked at **8.93%** during the week of December 7, 2020, then declined through January.
- Mobile converted at **6.26%**, compared with **5.91%** for desktop. The difference was borderline statistically significant and small in practical terms.
- Direct traffic converted at **5.92%**, Google organic at **5.08%**, and Google CPC at **4.74%**. These fields represent first-user acquisition rather than session-level attribution.
- Several high-traffic products converted at only 1–2%, creating candidates for inventory, tracking, merchandising, and product-page review.

![Weekly conversion trend](images/weekly_conversion_trend.png)

### Tracking health

The monitoring prototype combines a rolling seven-day baseline, event-volume ratio, z-score, page-view context, and traffic-adjusted event ratio.

It correctly surfaced the four manually validated `add_to_cart` outages from November 21–24, when event counts fell to zero despite continued site traffic. It separately classified two broader volume drops as likely traffic declines instead of event-specific tracking failures.

![Tracking-health alerts](images/tracking_health_alerts.png)

### Purchase propensity

The model predicts whether a purchase will occur later in a session using only information available at the first `view_item` event.

| Metric | Test result |
|---|---:|
| PR-AUC | **0.1402** |
| No-skill PR-AUC | 0.0504 |
| ROC-AUC | 0.7876 |
| Calibrated Brier score | 0.0457 |
| Top-decile lift | **3.13×** |
| Purchases captured in top decile | **31.2%** |

To prevent leakage, the pipeline uses chronological train/validation/test splits, fits preprocessing on training data only, excludes post-view behavior, and performs calibration and threshold selection on validation data only.

![Purchase rate by predicted-risk decile](images/model_decile_lift.png)

## Technical approach

| Area | Implementation |
|---|---|
| Data source | `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*` |
| Querying | BigQuery Standard SQL with `_TABLE_SUFFIX` cost controls and nested-field handling |
| Funnel logic | Session key from user ID + GA session ID; timestamp-validated stage ordering |
| Analysis | pandas, NumPy, SciPy, statsmodels |
| Modeling | scikit-learn pipelines, logistic regression, random forest, sigmoid calibration |
| Evaluation | Chronological holdout, PR-AUC, ROC-AUC, Brier score, lift, capture rate |
| Visualization | Plotly, Matplotlib, Seaborn |
| Application | Multi-page Streamlit dashboard using local CSV/JSON artifacts |

## Repository structure

```text
.
├── app.py                 # Streamlit Cloud entry point
├── dashboard/            # Six-page results application
├── data/processed/demo/  # Deployment-safe analytical artifacts
├── docs/                 # Metric definitions and data dictionary
├── images/               # Exported analysis visuals
├── notebooks/            # Statistical, monitoring, and ML workflows
├── sql/                  # BigQuery analysis, feature, and validation queries
└── requirements.txt
```

Notable files:

- [`sql/05_ordered_session_funnel.sql`](sql/05_ordered_session_funnel.sql) — timestamp-validated funnel
- [`sql/09_model_features.sql`](sql/09_model_features.sql) — leakage-safe feature engineering
- [`sql/12_tracking_health_monitor.sql`](sql/12_tracking_health_monitor.sql) — event-health signals
- [`sql/13_model_feature_validation.sql`](sql/13_model_feature_validation.sql) — feature quality checks
- [`notebooks/03_purchase_prediction.ipynb`](notebooks/03_purchase_prediction.ipynb) — model training and evaluation
- [`dashboard/README.md`](dashboard/README.md) — dashboard pages and artifact inputs

## Run the dashboard locally

Python 3.11 or newer is recommended.

```bash
git clone https://github.com/JasonValade/google-store-funnel-analysis.git
cd google-store-funnel-analysis

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open `http://localhost:8501`. The dashboard uses pre-computed files from `data/processed/demo/`; BigQuery credentials and environment variables are not required.

## Reproduce the analysis

The SQL files are numbered in execution order from schema inspection through model-feature validation. BigQuery Sandbox can query the public dataset without storing credentials in this repository.

The purchase-model notebook reads the included compressed feature extract directly:

```bash
python -m jupyter notebook notebooks/03_purchase_prediction.ipynb
```

Do not commit raw exports, service-account files, or credentials. Only small, aggregated, non-sensitive demo artifacts belong in `data/processed/demo/`.

## Recommendations

- Test ways to reduce product-view and cart-to-checkout friction, including clearer shipping information and a stronger checkout path.
- Audit high-traffic, zero-purchase products for availability, catalog consistency, and instrumentation before treating them as merchandising failures.
- Investigate self-referrals and attribution quality before reallocating acquisition budgets.
- Productionize event-health checks with scheduled queries and automated notifications.
- Monitor model calibration and purchase-rate drift before using propensity scores operationally.

These are testable hypotheses, not causal conclusions. Conversion changes should be evaluated through controlled experiments.

## Limitations

- The public dataset is obfuscated and covers only November 2020 through January 2021.
- `add_to_cart` tracking was unreliable November 1–15 and unavailable November 21–24.
- Acquisition fields describe first-user source/medium, not necessarily the source of each session.
- Product names were normalized because item identifiers were inconsistent across event types.
- The analysis is observational; segment differences and model associations do not establish causality.
- The dashboard is a portfolio application with static artifacts, not a live scoring or production alerting service.

## Author

Jason Valade · [LinkedIn](https://www.linkedin.com/in/jason-valade)
