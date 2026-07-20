-- 03_user_funnel.sql
-- Purpose: User-level funnel (view_item -> add_to_cart -> begin_checkout -> purchase)
-- Counts users who have at least one event of each type in the period.
-- Use _TABLE_SUFFIX to restrict dates. Start with small date window to validate.

WITH events AS (
  SELECT
    user_pseudo_id,
    event_name
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),

user_flags AS (
  SELECT
    user_pseudo_id,
    MAX(CASE WHEN event_name = 'view_item' THEN 1 ELSE 0 END) AS viewed_item,
    MAX(CASE WHEN event_name = 'add_to_cart' THEN 1 ELSE 0 END) AS added_to_cart,
    MAX(CASE WHEN event_name = 'begin_checkout' THEN 1 ELSE 0 END) AS began_checkout,
    MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) AS purchased
  FROM events
  GROUP BY user_pseudo_id
),

summary AS (
  SELECT
    COUNT(1) AS total_users,
    SUM(viewed_item) AS users_view_item,
    SUM(added_to_cart) AS users_add_to_cart,
    SUM(began_checkout) AS users_begin_checkout,
    SUM(purchased) AS users_purchase
  FROM user_flags
)

SELECT
  total_users,
  users_view_item,
  users_add_to_cart,
  users_begin_checkout,
  users_purchase,
  SAFE_DIVIDE(users_add_to_cart, NULLIF(users_view_item,0)) AS convert_view_to_add,
  SAFE_DIVIDE(users_begin_checkout, NULLIF(users_add_to_cart,0)) AS convert_add_to_begin_checkout,
  SAFE_DIVIDE(users_purchase, NULLIF(users_begin_checkout,0)) AS convert_begin_checkout_to_purchase,
  SAFE_DIVIDE(users_purchase, NULLIF(users_view_item,0)) AS overall_convert_view_to_purchase
FROM summary;

-- Notes:
-- * This is a user-level funnel; each user is counted once per stage if they have any matching event in the period.
-- * For session-level analysis, use sql/04_session_funnel.sql.
