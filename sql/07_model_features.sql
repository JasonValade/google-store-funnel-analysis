-- 07_model_features.sql
-- Purpose: Build a user-level modeling table for Python modeling
-- Target: purchased (1 if user has any purchase event, else 0)
-- Features: device category, source, medium, country, total_events, product_views, add_to_cart_count, begin_checkout_count, engagement_time_msec (sum where available)
-- IMPORTANT: Exclude features that would leak the purchase (e.g., revenue from purchase event or event timestamps that occur only after purchase).

WITH raw AS (
  SELECT
    user_pseudo_id,
    event_name,
    event_timestamp,
    event_date,
    device.category AS device_category,
    traffic_source.source AS source,
    traffic_source.medium AS medium,
    geo.country AS country,
    event_params
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),

-- Extract engagement_time_msec when available
engagement AS (
  SELECT
    user_pseudo_id,
    SUM(COALESCE((SELECT SAFE_CAST(ep.value.int_value AS FLOAT64) FROM UNNEST(event_params) ep WHERE ep.key = 'engagement_time_msec' LIMIT 1), 0)) AS engagement_time_msec
  FROM raw
  GROUP BY user_pseudo_id
),

user_agg AS (
  SELECT
    user_pseudo_id,
    ANY_VALUE(device_category) AS device_category,
    ANY_VALUE(source) AS source,
    ANY_VALUE(medium) AS medium,
    ANY_VALUE(country) AS country,
    COUNT(1) AS total_events,
    SUM(CASE WHEN event_name = 'view_item' THEN 1 ELSE 0 END) AS product_view_events,
    SUM(CASE WHEN event_name = 'add_to_cart' THEN 1 ELSE 0 END) AS add_to_cart_events,
    SUM(CASE WHEN event_name = 'begin_checkout' THEN 1 ELSE 0 END) AS begin_checkout_events,
    MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) AS purchased_flag
  FROM raw
  GROUP BY user_pseudo_id
)

SELECT
  u.user_pseudo_id,
  COALESCE(u.device_category, '(unknown)') AS device_category,
  COALESCE(u.source, '(unknown)') AS source,
  COALESCE(u.medium, '(unknown)') AS medium,
  COALESCE(u.country, '(unknown)') AS country,
  u.total_events,
  u.product_view_events,
  u.add_to_cart_events,
  u.begin_checkout_events,
  COALESCE(e.engagement_time_msec, 0) AS engagement_time_msec,
  u.purchased_flag AS purchased
FROM user_agg u
LEFT JOIN engagement e USING (user_pseudo_id);

-- Recommendation: Save the result of this query as `model_features` table or export to CSV for modeling in Python.
-- When exporting, ensure no PII is present. user_pseudo_id can be retained as an opaque identifier or removed if not required.
