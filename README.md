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

Notes on BigQuery access and billing

- BigQuery can be used in several modes. A billing-enabled Google Cloud project is required to run queries that create tables or run jobs that exceed the free limits.
- BigQuery Sandbox: Google offers a free BigQuery Sandbox tier that lets you query many public datasets (including `bigquery-public-data`) without a credit card, subject to free quotas and limits. Sandbox is suitable for exploration and small analyses. Check https://cloud.google.com/bigquery/docs/sandbox for limits and eligibility.
- Recommended permissions for analysis tasks: the minimal role required to run queries is `roles/bigquery.jobUser` (BigQuery Job User). Do NOT grant broad editor permissions by default. `BigQuery Data Editor` (or equivalent) is only required if you will create or write tables into a project dataset.

---

## Repository structure

google-store-funnel-analysis/
├── README.md                       <- This file
├── requirements.txt                <- Python dependencies
├── .gitignore                      <- Files to ignore from git
├── sql/                            <- Parameterized BigQuery SQL queries (canonical files: run in numeric order 00 → 11)
│   ├── 00_schema_inspection.sql
│   ├── 01_data_exploration.sql
│   ├── 02_data_quality.sql
│   ├── 03_user_funnel.sql
│   ├── 04_session_funnel.sql
│   ├── 05_ordered_session_funnel.sql
│   ├── 06_device_analysis.sql
│   ├── 07_traffic_source_analysis.sql
│   ├── 08_product_analysis.sql
│   ├── 09_model_features.sql
│   ├── 10_dashboard_tables.sql
│   ├── 11_weekly_conversion_trend.sql
│   └── archive/                    <- Obsolete/prior versions (do not use for analysis)
├── notebooks/                      <- Analysis and modeling notebooks (placeholders)
│   ├── 01_statistical_analysis.ipynb
│   └── 02_purchase_prediction.ipynb
├── data/
│   ├── raw/                        <- Place raw exports here (gitignored)
│   └── processed/                  <- Place processed CSVs / query outputs here; small demo CSVs may be committed under data/processed/demo/
├── docs/                           <- Metric definitions and data dictionary
├── dashboard/                      <- Dashboard plan and assets
├── images/                         <- Images used in README / reports
└── reports/                        <- Exported reports and slides (placeholders)

---

## Metric definitions (summary)

- User: Identified by user_pseudo_id in GA4 export
- Event: A GA4 event (e.g., view_item, add_to_cart, begin_checkout, purchase)
- Session: Identified by the GA4 session identifier (ga_session_id) when available; session_id here is defined as CONCAT(user_pseudo_id, '_', ga_session_id)
- Transaction / Purchase: A completed purchase event (event_name = 'purchase'); transaction revenue may appear on the event or within items — inspect schema to confirm
- Funnel stages: view_item -> add_to_cart -> begin_checkout -> purchase
- Conversion rate (stage A -> B): SAFE_DIVIDE(count_reached_B, count_reached_A)
- Drop-off rate: 1 - conversion rate
- Revenue: explicitly defined as either ITEM revenue (SUM(item.price * item.quantity) for purchase events) or TRANSACTION revenue (as reported on purchase events). Confirm which field is present before using transaction revenue.
- Traffic source: Top-level traffic_source fields commonly reflect first-user acquisition (the source/medium that brought the user). See docs/metric_definitions.md and run sql/00_schema_inspection.sql to check whether session-level campaign parameters or a collected_traffic_source field exist before interpreting these as session attribution.

---

## Methodology

1. Run `sql/00_schema_inspection.sql` to inspect schema, event_param keys, and item fields in this dataset. Adapt subsequent queries based on what you find.
2. Run data-exploration and data-quality queries (sql/01_data_exploration.sql and sql/02_data_quality.sql) over a small date window to validate event names and nested schemas.
3. Build the user-level funnel (sql/03_user_funnel.sql) and validate counts. This is the primary gating step before any modeling.
4. Build session-level funnels (sql/04_session_funnel.sql) and ordered session funnels (sql/05_ordered_session_funnel.sql) to analyze within-session behavior and verify event ordering.
5. Produce product and channel aggregates and export validated, small aggregated CSVs (if publishing demo results) under data/processed/demo/.
6. After funnel validation, create model features (sql/09_model_features.sql) using an explicit prediction moment and observation window. Do NOT include features observed after the prediction cutoff.
7. Run product analysis (sql/08_product_analysis.sql) to identify high-traffic, low-conversion opportunities. Review data-quality notes in that query.
8. Run weekly conversion trend analysis (sql/11_weekly_conversion_trend.sql) to observe seasonal or temporal patterns. Document findings with appropriate caveats about partial weeks and observational limits.

---

## Running the SQL and notebooks

1. If you have a billing-enabled Google Cloud project, you can run queries that create tables or export results. If you prefer not to attach billing, try BigQuery Sandbox for exploratory queries on public datasets (subject to Sandbox limits).
2. Open the public dataset in BigQuery and preview the tables (instructions in README below).
3. Run `sql/00_schema_inspection.sql` first to identify available event_params keys and item fields. Use that to adapt revenue and session extraction logic in later queries.
4. Run the exploration and data-quality queries (01 and 02) on a small date range (e.g., one week) to preview costs and schema.
5. Run the user-level and session-level funnel queries (03_user_funnel.sql, 04_session_funnel.sql, 05_ordered_session_funnel.sql). Save outputs that will be used in notebooks under `data/processed/` or as BigQuery tables in your own project. Recommended outputs to save:
   - data/processed/user_funnel.csv (from sql/03_user_funnel.sql)
   - data/processed/session_funnel.csv (from sql/04_session_funnel.sql)
   - data/processed/ordered_session_funnel.csv (from sql/05_ordered_session_funnel.sql)
   - data/processed/funnel_by_device.csv (from sql/04_device_analysis.sql)
   - data/processed/funnel_by_traffic.csv (from sql/05_traffic_source_analysis.sql)
   - data/processed/product_metrics.csv (from sql/06_product_analysis.sql)
   - data/processed/model_features.csv (from sql/07_model_features.sql) — only after funnel validation and explicit feature-cutoff choices
6. Update notebook file paths to point to these CSVs. Each notebook explains how the input file is generated.

**Validated SQL queries (executed successfully in BigQuery)**:
- `sql/08_product_analysis.sql` — Product opportunity analysis with revenue and opportunity rankings (validated)
- `sql/11_weekly_conversion_trend.sql` — Weekly session-level funnel analysis (validated)

**Other SQL queries** (syntax validated but not yet executed in this environment):
- sql/00 through sql/07, sql/09_model_features.sql, sql/10_dashboard_tables.sql

Important: Do not commit credentials, service-account files, or sensitive exports. Small, aggregated, non-sensitive demo CSVs may be committed to data/processed/demo/ for portfolio demonstration.

---

## Dashboard plan

See `dashboard/README.md` for a step-by-step plan to create a dashboard in Looker Studio, Tableau, or Power BI.

---

## Findings, visualizations, recommendations

**Status**: The product opportunity analysis and weekly conversion trend analysis have been documented with validated findings below. Dashboard development, final business recommendations, and optional predictive modeling remain unfinished.


### Product Analysis Data Quality

This project uses normalized product names (LOWER(TRIM(item.item_name))) as the product-analysis key for the following reasons:

- **Item ID reliability**: Item IDs alone were not reliable for joining product views and purchases. Purchase events contained 810 distinct item IDs, while view_item events contained only 427.
- **Normalized name consistency**: Normalized product names were substantially more consistent across event types:
  - 388 normalized product names appeared in both view_item and purchase events
  - 34 appeared only in view_item events
  - 8 appeared only in purchase events
  - Matching product names covered 93.55% of product-view sessions and 96.19% of purchase sessions
- **Key selection**: Therefore, normalized product names were selected as the product-analysis key.

**Important caveat**: Products with zero purchases must be treated as **investigation candidates**, not automatically as poorly designed product pages. Possible explanations include unavailable products, discontinued items, catalog changes, data obfuscation, or tracking issues.

### Product Opportunity Findings

Query: `sql/08_product_analysis.sql`  
Unit of analysis: sessions (product-view sessions and purchase sessions are counted as distinct sessions)  
Minimum threshold: 1,000 product-view sessions  
Analysis period: 2020-11-01 through 2021-01-31  

**Top revenue products**:
- Google Zip Hoodie F/C: $13,788 item revenue
- Google Crewneck Sweatshirt Navy: $10,714 item revenue
- Google Men's Tech Fleece Grey: $9,965 item revenue

**High-traffic, low-conversion candidates**:
- Several apparel products had purchase rates of 1–2%, making them candidates for investigation into product pages, pricing, availability, or customer experience barriers.
- Google Canteen Bottle Black maintained a 4.48% product purchase rate, indicating stronger conversion in the accessories category.

**Investigation status categories**:
- **"Investigate availability or tracking"**: Products with zero purchases. These may indicate catalog changes, discontinued items, or potential tracking problems.
- **"High-traffic, low-conversion candidate"**: Products with purchase rates below 1% despite traffic above 1,000 sessions.
- **"Monitor"**: Products with purchase rates ≥1%.

**Important interpretation**: These observational conversion rates describe traffic patterns and potential opportunities, not proof of product page quality or design effectiveness. Improving conversion rates would require targeted A/B testing and controlled experiments.

### Weekly Conversion Trend

Query: `sql/11_weekly_conversion_trend.sql`  
Unit of analysis: sessions (ordered session-level funnel)  
Funnel stages: view_item (earliest) → begin_checkout (at or after view_item) → purchase (at or after begin_checkout)  
Week assignment: DATE_TRUNC(view_date, WEEK(MONDAY)) based on earliest product-view date in each session  
Analysis period: 2020-11-01 through 2021-01-31  

**Observed trends**:
- Purchase conversion increased through November, peaking at **8.93%** during the week beginning 2020-12-07.
- Following the peak, conversion declined:
  - 7.39% for the week beginning 2020-12-14
  - 5.44% for the week beginning 2020-12-21
  - 4.24% for the week beginning 2020-12-28
  - 3.56% for the week beginning 2021-01-04
- The decline was primarily associated with fewer product-view sessions progressing to checkout (a decrease in the view-to-checkout rate).

**Limitations and caveats**:
- The week beginning 2020-10-26 is a **partial week** (contains only November 1 onward, as the dataset begins on a Sunday) and should be excluded from trend analysis and visualizations.
- Weekly trends are **descriptive** and based on observational data. They do not establish causation.
- The final week in the dataset (beginning 2021-01-25) may be incomplete if sessions are ongoing at the dataset boundary.

---

## Limitations and Non-Causal Interpretation

**Observational data**: This analysis is based on observational GA4 data, not controlled experiments. Observed differences in conversion rates, traffic patterns, or product performance do not establish causation.

**Statistical vs. practical significance**: Statistical tests in the notebooks (e.g., z-tests for device comparison) identify whether observed differences are likely real; they do not confirm that causation exists or that the difference is actionable.

**Product conversion rates**: Differences in product purchase rates may reflect product quality, pricing, availability, customer perception, or tracking issues. Low conversion does not automatically indicate a poor product page; further investigation is required.

**Session attribution**: This analysis uses session-level ordering (view_item → begin_checkout → purchase) to construct the funnel. Session-level conversion rates reflect the proportion of product-view sessions that result in purchases within that session, not user-level lifetime value or long-term customer behavior.

**Seasonal and external factors**: Weekly conversion trends may be influenced by external factors (holiday shopping, marketing campaigns, competitive activity, stock availability) not captured in this GA4 dataset.

**Next steps**: To improve conversion rates or understand causal drivers, consider:
- A/B testing hypothesized improvements (checkout flow, product pages, pricing strategies)
- Qualitative research (user interviews, session replay) to understand abandonment reasons
- Cohort analysis to understand user segments and their behaviors
- Causal inference methods (propensity matching, instrumental variables) if confounders can be controlled

---

## Future improvements

- Enrich features with sessionization and time-between-events metrics
- Add uplift or causal inference methods before recommending interface changes
- A/B test hypothesized fixes (e.g., mobile checkout flow tweaks)

---

## Contact

Author: Jason Valade / www.linkedin.com/in/jason-valade

