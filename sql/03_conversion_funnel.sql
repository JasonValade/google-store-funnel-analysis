-- 03_conversion_funnel.sql
-- Purpose: Build a user-level conversion funnel (view_item -> add_to_cart -> begin_checkout -> purchase)
-- Outputs counts at each stage, stage-to-stage conversion, and drop-offs.
-- Adjust _TABLE_SUFFIX range (start_date / end_date) before running.

WITH events AS (
  SELECT
    user_pseudo_id,
    event_timestamp,
    event_name,
    event_date,
    device,
    traffic_source,
    event_params
  FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE
    _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),

-- Aggregate events to user-level flags for each funnel stage
user_stage_flags AS (
  SELECT
    user_pseudo_id,
    MIN(event_date) AS first_event_date,
    MAX(CASE WHEN event_name = 'view_item' THEN 1 ELSE 0 END) AS viewed_item,
    MAX(CASE WHEN event_name = 'add_to_cart' THEN 1 ELSE 0 END) AS added_to_cart,
    MAX(CASE WHEN event_name = 'begin_checkout' THEN 1 ELSE 0 END) AS began_checkout,
    MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) AS purchased
  FROM events
  GROUP BY user_pseudo_id
),

funnel_counts AS (
  SELECT
    'users_with_view_item' AS stage, COUNT(1) AS users_reached
  FROM user_stage_flags
  WHERE viewed_item = 1
  UNION ALL
  SELECT 'users_with_add_to_cart', COUNT(1) FROM user_stage_flags WHERE added_to_cart = 1
  UNION ALL
  SELECT 'users_with_begin_checkout', COUNT(1) FROM user_stage_flags WHERE began_checkout = 1
  UNION ALL
  SELECT 'users_with_purchase', COUNT(1) FROM user_stage_flags WHERE purchased = 1
),

-- Pivoted counts for computing conversion rates
summary AS (
  SELECT
    SUM(viewed_item) AS users_view_item,
    SUM(added_to_cart) AS users_add_to_cart,
    SUM(began_checkout) AS users_begin_checkout,
    SUM(purchased) AS users_purchase,
    COUNT(1) AS total_users
  FROM user_stage_flags
)

SELECT
  users_view_item,
  users_add_to_cart,
  users_begin_checkout,
  users_purchase,
  SAFE_DIVIDE(users_add_to_cart, users_view_item) AS convert_view_to_add,
  SAFE_DIVIDE(users_begin_checkout, users_add_to_cart) AS convert_add_to_begin_checkout,
  SAFE_DIVIDE(users_purchase, users_begin_checkout) AS convert_begin_checkout_to_purchase,
  SAFE_DIVIDE(users_purchase, users_view_item) AS overall_convert_view_to_purchase,
  1 - SAFE_DIVIDE(users_add_to_cart, users_view_item) AS dropoff_view_to_add,
  1 - SAFE_DIVIDE(users_begin_checkout, users_add_to_cart) AS dropoff_add_to_begin_checkout,
  1 - SAFE_DIVIDE(users_purchase, users_begin_checkout) AS dropoff_begin_checkout_to_purchase
FROM summary;

-- Notes:
-- * This is a user-level funnel (counts each user once). For session-level funnels, sessionization is required
-- * Use the model_features query to create a labeled table for modeling (includes purchased flag and features)
