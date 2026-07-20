-- 05_traffic_source_analysis.sql
-- Purpose: Compare funnel performance by traffic_source.source and traffic_source.medium
-- Use this to identify high-traffic but low-converting channels

WITH events AS (
  SELECT
    user_pseudo_id,
    event_name,
    traffic_source.source AS source,
    traffic_source.medium AS medium
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),

user_channel_flags AS (
  SELECT
    COALESCE(source, '(unknown)') AS source,
    COALESCE(medium, '(unknown)') AS medium,
    user_pseudo_id,
    MAX(CASE WHEN event_name = 'view_item' THEN 1 ELSE 0 END) AS viewed_item,
    MAX(CASE WHEN event_name = 'add_to_cart' THEN 1 ELSE 0 END) AS added_to_cart,
    MAX(CASE WHEN event_name = 'begin_checkout' THEN 1 ELSE 0 END) AS began_checkout,
    MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) AS purchased
  FROM events
  GROUP BY source, medium, user_pseudo_id
),

channel_summary AS (
  SELECT
    source,
    medium,
    SUM(viewed_item) AS users_view_item,
    SUM(added_to_cart) AS users_add_to_cart,
    SUM(began_checkout) AS users_begin_checkout,
    SUM(purchased) AS users_purchase
  FROM user_channel_flags
  GROUP BY source, medium
)

SELECT
  source,
  medium,
  users_view_item,
  users_add_to_cart,
  users_begin_checkout,
  users_purchase,
  SAFE_DIVIDE(users_add_to_cart, users_view_item) AS convert_view_to_add,
  SAFE_DIVIDE(users_purchase, users_view_item) AS overall_convert_view_to_purchase
FROM channel_summary
ORDER BY users_view_item DESC
LIMIT 200;

-- Notes:
-- * For channel analysis, consider aggregating similar sources/mediums (e.g., organic search)
-- * Save results, then investigate channels with high traffic but low overall conversion rate
