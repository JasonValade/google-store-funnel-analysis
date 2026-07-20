-- 11_weekly_conversion_trend.sql
-- Purpose: Session-level ordered weekly funnel analysis.
-- Unit of analysis: sessions
-- Analysis period: 2020-11-01 through 2021-01-31
-- Funnel stages: view_item (earliest in session) → begin_checkout (at or after view_item) → purchase (at or after begin_checkout)
-- Week assignment: Based on the earliest product-view date in each session, using DATE_TRUNC(view_date, WEEK(MONDAY))

-- IMPORTANT: The week beginning 2020-10-26 contains only November 1 because the dataset starts on a Sunday.
-- This is a partial week and should be excluded from week-over-week trend analysis and visualizations.

WITH raw AS (
  SELECT
    user_pseudo_id,
    event_name,
    event_timestamp,
    event_date,
    TIMESTAMP_MICROS(event_timestamp) AS event_ts,
    (SELECT COALESCE(CAST(ep.value.int_value AS STRING), ep.value.string_value) FROM UNNEST(event_params) ep WHERE ep.key = 'ga_session_id' LIMIT 1) AS ga_session_id
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),

-- Build session identifiers
sessions_raw AS (
  SELECT
    CONCAT(user_pseudo_id, '_', COALESCE(ga_session_id, 'unknown')) AS session_id,
    user_pseudo_id,
    event_name,
    event_timestamp,
    event_date
  FROM raw
),

-- Find the earliest timestamp for each funnel stage within each session
session_event_times AS (
  SELECT
    session_id,
    MIN(CASE WHEN event_name = 'view_item' THEN event_timestamp END) AS t_view_item,
    MIN(CASE WHEN event_name = 'view_item' THEN event_date END) AS view_date,
    MIN(CASE WHEN event_name = 'begin_checkout' THEN event_timestamp END) AS t_begin_checkout,
    MIN(CASE WHEN event_name = 'purchase' THEN event_timestamp END) AS t_purchase
  FROM sessions_raw
  GROUP BY session_id
),

-- Assign weeks based on view_date (earliest product-view date)
-- and count sessions reaching each stage with proper ordering.
-- Ordering validation: checkout is counted only when checkout_timestamp >= view_timestamp.
--   Purchase is counted only when purchase_timestamp >= checkout_timestamp (or view_timestamp if no checkout).
session_flags AS (
  SELECT
    session_id,
    DATE_TRUNC(view_date, WEEK(MONDAY)) AS week_start,
    MAX(CASE WHEN t_view_item IS NOT NULL THEN 1 ELSE 0 END) AS viewed_product,
    MAX(CASE WHEN t_begin_checkout IS NOT NULL AND t_begin_checkout >= t_view_item THEN 1 ELSE 0 END) AS began_checkout_ordered,
    MAX(CASE WHEN t_purchase IS NOT NULL AND t_purchase >= COALESCE(t_begin_checkout, t_view_item) THEN 1 ELSE 0 END) AS purchased_ordered
  FROM session_event_times
  WHERE view_date IS NOT NULL
  GROUP BY session_id, week_start
),

-- Weekly aggregation: count sessions at each stage and compute conversion rates
weekly_summary AS (
  SELECT
    week_start,
    COUNT(1) AS total_sessions,
    SUM(viewed_product) AS product_view_sessions,
    SUM(began_checkout_ordered) AS checkout_sessions,
    SUM(purchased_ordered) AS purchase_sessions
  FROM session_flags
  GROUP BY week_start
)

SELECT
  week_start,
  product_view_sessions,
  checkout_sessions,
  purchase_sessions,
  SAFE_DIVIDE(checkout_sessions, NULLIF(product_view_sessions, 0)) AS view_to_checkout_rate,
  SAFE_DIVIDE(purchase_sessions, NULLIF(checkout_sessions, 0)) AS checkout_to_purchase_rate,
  SAFE_DIVIDE(purchase_sessions, NULLIF(product_view_sessions, 0)) AS purchase_conversion_rate
FROM weekly_summary
ORDER BY week_start ASC;

-- Notes and methodology:
-- * Unit: sessions. Weekly conversion is based on ordered sessions (events must occur in proper timestamp sequence), not users or raw event counts.
-- * Timestamp ordering: checkout_timestamp >= view_timestamp; purchase_timestamp >= checkout_timestamp (or view_timestamp if no checkout).
-- * Week assignment: Each session is assigned the week containing its earliest product-view date (view_item event).
-- * Ordering validation: Checkout is counted only when begin_checkout timestamp occurs at or after the first view_item timestamp in the session.
--   Purchase is counted only when purchase timestamp occurs at or after the checkout time (or view_item if no checkout).
-- * Partial week: The week beginning 2020-10-26 contains only November 1 (dataset starts on a Sunday) and should be excluded from trend analysis.
-- * Dataset boundary: The final week (beginning 2021-01-25) may be incomplete if some sessions end at the dataset boundary. Always document the analysis period.
