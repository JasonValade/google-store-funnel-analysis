# Dashboard plan

This document outlines how to create a dashboard (Looker Studio / Tableau / Power BI) to present the funnel analysis and product opportunities.

Essential charts and elements

- KPI header: Total users, Purchases, Revenue, Overall conversion rate (purchases / users)
- Funnel visualization: stacked or step chart showing counts at each stage: view_item -> add_to_cart -> begin_checkout -> purchase
- Device comparison: bar chart comparing conversion rates by device_category (mobile, desktop, tablet)
- Traffic-source performance: table and bar charts by source/medium showing users, purchases, conversion rate, revenue
- Revenue over time: time series of revenue and purchases by day or week
- Product-opportunity table: products with high views but low purchase conversion (focus for merchandising or UX experiments)
- Filters: date range, device, channel/source

Data sources

- Use BigQuery tables or exported CSVs from the SQL scripts in the `sql/` folder.
- Recommended tables to export/import into your dashboard tool: user_funnel, funnel_by_device, funnel_by_traffic, product_metrics, model_features (aggregates only)

Looker Studio notes

- Connect to BigQuery and select the dataset/table exported to your project
- Build calculated fields for conversion rates using SAFE_DIVIDE
- Use date filters and parameter controls for date range

Tableau / Power BI notes

- Import BigQuery tables via native connectors or CSV exports
- Use calculated fields to compute rates and drop-offs

Design tips

- Emphasize relative drop-offs (stage-to-stage) and device differences
- Include a clear explanation of limitations and that analyses are observational
- Provide actionable recommendations next to opportunities (e.g., "Investigate mobile checkout friction for product X")
