-- 04_device_analysis.sql
-- Purpose: Compare funnel performance by device category (e.g., mobile, desktop, tablet)
-- Reuses the user-stage logic but groups by device.category

WITH events AS (
  SELECT
    user_pseudo_id,
    event_name,
    device.category AS device_category
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),

user_device_flags AS (
  SELECT
    device_category,
    user_pseudo_id,
    MAX(CASE WHEN event_name = 'view_item' THEN 1 ELSE 0 END) AS viewed_item,
    MAX(CASE WHEN event_name = 'add_to_cart' THEN 1 ELSE 0 END) AS added_to_cart,
    MAX(CASE WHEN event_name = 'begin_checkout' THEN 1 ELSE 0 END) AS began_checkout,
    MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) AS purchased
  FROM events
  GROUP BY device_category, user_pseudo_id
),

device_summary AS (
  SELECT
    device_category,
    SUM(viewed_item) AS users_view_item,
    SUM(added_to_cart) AS users_add_to_cart,
    SUM(began_checkout) AS users_begin_checkout,
    SUM(purchased) AS users_purchase
  FROM user_device_flags
  GROUP BY device_category
)

SELECT
  device_category,
  users_view_item,
  users_add_to_cart,
  users_begin_checkout,
  users_purchase,
  SAFE_DIVIDE(users_add_to_cart, users_view_item) AS convert_view_to_add,
  SAFE_DIVIDE(users_begin_checkout, users_add_to_cart) AS convert_add_to_begin_checkout,
  SAFE_DIVIDE(users_purchase, users_begin_checkout) AS convert_begin_checkout_to_purchase,
  SAFE_DIVIDE(users_purchase, users_view_item) AS overall_convert_view_to_purchase
FROM device_summary
ORDER BY users_view_item DESC;

-- Notes:
-- * device.category may be NULL for some rows; consider coalescing to 'unknown' if desired
-- * Interpret differences cautiously; these are observational comparisons
