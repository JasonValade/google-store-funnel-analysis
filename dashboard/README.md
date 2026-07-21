# Dashboard — V4 Streamlit Results App

A multi-page Streamlit dashboard presenting pre-computed analytics and model
results from the Google Merchandise Store funnel analysis project (Nov 2020 – Jan 2021).

**Offline portfolio prototype — no BigQuery access or Google credentials required.**
All data is loaded from pre-computed CSV and JSON artifacts in `data/processed/demo/`.

---

## Pages

| Page | File | Contents |
|---|---|---|
| Executive Overview | `pages/00_executive_overview.py` (routed by `app.py`) | KPI cards, primary funnel, weekly trend, version highlights |
| Funnel & Conversion Trends | `pages/01_funnel_trends.py` | Date-filtered weekly trend, funnel chart, stage metrics, download |
| Device & Product Insights | `pages/02_device_product_insights.py` | Device bar chart, product-opportunity table with filters and download |
| Tracking Health | `pages/03_tracking_health.py` | Alert timeline, ratio scatter chart, methodology explanation |
| Purchase Propensity Model | `pages/04_purchase_propensity.py` | PR curves, calibration, decile lift, confusion matrix, split table |
| Methodology & Limitations | `pages/05_methodology.py` | Dataset, funnel/model methodology, limitations, repository paths |

---

## Data sources

All data is loaded from `data/processed/demo/`:

| File | Description |
|---|---|
| `device_funnel.csv` | 3-row device-level funnel summary |
| `weekly_conversion.csv` | 14-row weekly conversion rates |
| `tracking_alerts.csv` | 6-row tracking alert log |
| `model_features.csv.gz` | 77,020-row session-level model features (gzip) |
| `model_metrics.json` | 36-key model evaluation summary |
| `model_validation_comparison.csv` | 3-row validation comparison table |
| `model_pr_curves.csv` | Precision-recall curve data (long format) |
| `model_calibration_curves.csv` | Calibration curve data (test set) |
| `model_test_deciles.csv` | 10-row decile lift table |
| `model_logistic_coefficients.csv` | Top-20 LR feature associations |

---

## Local setup

### Prerequisites

- Python 3.11+ recommended
- A virtual environment (`.venv/` in the repo root)

### Install dependencies

```bash
pip install -r requirements.txt
```

Streamlit and Plotly are listed in `requirements.txt` under the **V4 Dashboard** section.

### Run the app

```bash
python -m streamlit run dashboard/app.py
```

The app will open at **http://localhost:8501** by default.
Navigate between pages using the sidebar.

---

## No credentials required

This app does not:
- Connect to BigQuery
- Require Google Cloud credentials or a service-account key
- Make network requests to any external service
- Require a GCP project ID

All analytical results were pre-computed from the BigQuery public dataset
(`bigquery-public-data.ga4_obfuscated_sample_ecommerce`) and saved as local
artifacts in `data/processed/demo/`. To regenerate artifacts, re-run
`notebooks/03_purchase_prediction.ipynb`.

---

## Deployment limitations

- **No live model:** The fitted Random Forest pipeline is not serialised in this
  repository. The Purchase Propensity page shows pre-computed evaluation results only.
- **No live data:** All charts and metrics are static, derived from the
  Nov 2020 – Jan 2021 analysis window.
- **Streamlit Community Cloud:** The app is designed to run locally or on
  Streamlit Community Cloud. Deploying publicly requires committing all
  `data/processed/demo/` artifacts (all files are < 4 MB individually).
  No secrets or environment variables are needed.

---

## Offline-results disclaimer

All findings are observational associations derived from an obfuscated public
dataset. Results are for portfolio demonstration only and should not be applied
to production decisions without replication on unobfuscated data.
The model identifies propensity associations and does not establish causal effects.
