# Google Merchandise Store Conversion Funnel Analysis

## Project overview

This repository contains a reproducible analysis project for the Google Merchandise Store public Google Analytics 4 (GA4) e-commerce dataset. The goal is to identify where users drop out of the purchase funnel, compare conversion performance across devices and channels, analyze products with strong traffic but low purchase conversion, and build an interpretable purchase prediction model.

This is a portfolio project scaffold — SQL query files, notebooks, and documentation are provided. The repository does NOT contain Google Cloud credentials or exported datasets. Queries are written for BigQuery and must be run in a Google Cloud project with BigQuery enabled.

Project name: Google Merchandise Store Conversion Funnel Analysis

NOTE: Do not execute any BigQuery jobs from this environment unless Google Cloud authentication is configured and you understand the potential costs.

---

## Business problem

Online retailers lose revenue when users drop out of the purchase funnel. Understanding where users abandon the funnel, which devices and channels underperform, and which products represent opportunities can drive targeted experiments and UX changes that increase conversions and revenue.

Research questions

- Where in the funnel (view_item -> add_to_cart -> begin_checkout -> purchase) do the largest drop-offs occur?
- Do mobile users convert at different rates than desktop users? Is the difference statistically significant and practically meaningful?
- Which traffic sources and mediums drive the most conversions and the highest revenue per user?
- Which products have high view/traffic but low purchase conversion (opportunity products)?
- Can an interpretable model (logistic regression) predict the probability a user will purchase, and which features are most predictive?

---

## Dataset

Public BigQuery dataset: bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*

This dataset contains GA4 event-level e-commerce data from 2020-11-01 through 2021-01-31 (obfuscated sample). The queries in this repo use _TABLE_SUFFIX filtering to limit scanned tables and cost.

Limitations

- This is a sample / obfuscated dataset and may not reflect a production property in all details.
- GA4 export schema is nested (arrays and RECORD types). Queries use UNNEST and safe extraction patterns but you may need to adapt field selections depending on exact table structure or schema changes.
- Observational differences do not imply causation. Statistical tests here are descriptive and hypothesis-generating.

---

## Technology stack

- Google BigQuery (SQL / GoogleSQL)
- Python 3
- pandas, numpy, matplotlib, seaborn, scipy, statsmodels, scikit-learn, jupyter
- Optional: Looker Studio / Tableau / Power BI for dashboarding

---

## Repository structure

google-store-funnel-analysis/
├── README.md                       <- This file
├── requirements.txt                <- Python dependencies
├── .gitignore                      <- Files to ignore from git
├── sql/                            <- Parameterized BigQuery SQL queries
│   ├── 01_data_exploration.sql
│   ├── 02_data_quality.sql
│   ├── 03_conversion_funnel.sql
│   ├── 04_device_analysis.sql
│   ├── 05_traffic_source_analysis.sql
│   ├── 06_product_analysis.sql
│   └── 07_model_features.sql
├── notebooks/                      <- Analysis and modeling notebooks (placeholders)
│   ├── 01_statistical_analysis.ipynb
│   └── 02_purchase_prediction.ipynb
├── data/
│   ├── raw/                        <- Place raw exports here (gitignored)
│   └── processed/                  <- Place processed CSVs / query outputs here (gitignored)
├── dashboard/                      <- Dashboard plan and assets
├── images/                         <- Images used in README / reports
└── reports/                         <- Exported reports and slides (placeholders)

---

## Metric definitions

- User: Identified by user_pseudo_id in GA4 export
- Event: A GA4 event (e.g., view_item, add_to_cart, begin_checkout, purchase)
- Funnel stages: view_item -> add_to_cart -> begin_checkout -> purchase
- Conversion rate (stage A -> B): users who reached B divided by users who reached A
- Drop-off rate: 1 - conversion rate
- Revenue: extracted from purchase events (see product queries for extraction logic)

---

## Methodology

1. Use the provided BigQuery SQL files to explore data, surface quality issues, and build a user-level funnel and aggregated tables.
2. Export processed query results (user-level funnel, product aggregates, modeling features) to CSV files in `data/processed/`.
3. Use the statistical notebook to compare device conversion rates and run hypothesis tests.
4. Use the modeling notebook to train and evaluate interpretable logistic regression models.
5. Use dashboard plan to create visualizations in Looker Studio / Tableau / Power BI.

---

## Running the SQL and notebooks

1. Create or select a Google Cloud project with billing enabled and BigQuery API activated (instructions below).
2. Open the public dataset in BigQuery and preview the tables (instructions below).
3. Copy the SQL files into the BigQuery console's query editor or run them via `bq` or client libraries. Each SQL file includes a header with recommended _TABLE_SUFFIX filters.
4. Save query outputs that are required for later steps as CSV or as a BigQuery table in your project. Recommended outputs to save in `data/processed/`:
   - user_funnel.csv (from 03_conversion_funnel.sql)
   - funnel_by_device.csv (from 04_device_analysis.sql)
   - funnel_by_traffic.csv (from 05_traffic_source_analysis.sql)
   - product_metrics.csv (from 06_product_analysis.sql)
   - model_features.csv (from 07_model_features.sql)
5. Open the notebooks in Jupyter / Colab. Update paths to point to the CSVs exported above. Notebooks contain placeholders where real outputs are required.

Important: Do not commit exported datasets or credentials to this repository.

---

## Dashboard plan

See `dashboard/README.md` for a step-by-step plan to create a dashboard in Looker Studio, Tableau, or Power BI.

---

## Findings, visualizations, recommendations

Placeholder sections for final report. Do not fabricate results — populate these after running the queries and notebooks.

---

## Future improvements

- Enrich features with sessionization and time-between-events metrics
- Add uplift or causal inference methods before recommending interface changes
- A/B test hypothesized fixes (e.g., mobile checkout flow tweaks)

---

## Contact

Author: (Your name) — add contact and portfolio links here

License: Use for portfolio/demo purposes only; do not upload private credentials.
