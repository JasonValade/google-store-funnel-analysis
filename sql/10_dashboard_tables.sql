-- 10_dashboard_tables.sql
-- Purpose: Templates for pre-aggregated dashboard tables. Unit of analysis noted per query.
-- Run after schema inspection and funnel validation.

-- 1) Daily KPIs (unit: daily events/users/purchases)
SELECT
  event_date,
  COUNT(DISTINCT user_pseudo_id) AS daily_users,
  SUM(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) AS daily_purchase_events
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
GROUP BY event_date
ORDER BY event_date;

-- 2) Daily revenue (two separate metrics):
--    a) transaction-level revenue (unit: transactions) — extract from purchase event params if present
--    b) item-level revenue (unit: item rows) — sum(item.item_revenue) or price*quantity fallback

-- Example (item-level revenue; unit: items)
SELECT
  event_date,
  SUM(CASE WHEN event_name = 'purchase' THEN COALESCE(SAFE_CAST(item.item_revenue AS FLOAT64), SAFE_CAST(item.price AS FLOAT64) * IFNULL(item.quantity,1)) ELSE 0 END) AS daily_item_revenue_estimate
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`, UNNEST(items) AS item
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
GROUP BY event_date
ORDER BY event_date;

-- 3) Funnel snapshot by device (session-level) — reuse sql/06_device_analysis.sql output as a table/view in your project for dashboarding.

-- 4) Product opportunity table (items unit): reuse sql/08_product_analysis.sql and expose top products by users_viewed with low view->purchase rate.

-- Notes:
-- * These are templates. For production dashboards, create materialized tables or scheduled queries in your own project and connect the dashboard to those tables for performance and cost control.
-- * Ensure you use consistent units (sessions vs items vs transactions) across charts and label them clearly in the dashboard.
