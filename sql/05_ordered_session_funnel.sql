-- 05_ordered_session_funnel.sql
-- Purpose: Count sessions where funnel events occurred in the specified order within the same session
-- Order: view_item -> add_to_cart -> begin_checkout -> purchase
-- Unit of analysis: sessions. This is the primary session-level ordered funnel analysis for website performance.
-- Uses ga_session_id extracted from event_params. Run sql/00_schema_inspection.sql first to confirm ga_session_id and event_timestamp units.

WITH raw AS (
  SELECT
    user_pseudo_id,
    event_name,
    event_timestamp,
    TIMESTAMP_MICROS(event_timestamp) AS event_ts_readable,
    (SELECT
       COALESCE(CAST(ep.value.int_value AS STRING), ep.value.string_value)
     FROM UNNEST(event_params) ep
     WHERE ep.key = 'ga_session_id'
     LIMIT 1) AS ga_session_id
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),

session_events AS (
  SELECT
    user_pseudo_id,
    COALESCE(ga_session_id, '(unknown)') AS ga_session_id,
    CONCAT(user_pseudo_id, '_', COALESCE(ga_session_id, 'unknown')) AS session_id,
    event_name,
    event_timestamp,
    event_ts_readable
  FROM raw
),

-- For each session, compute the earliest timestamp of each funnel event and readable equivalents
session_event_times AS (
  SELECT
    session_id,
    MIN(CASE WHEN event_name = 'view_item' THEN event_timestamp END) AS t_view_item,
    MIN(CASE WHEN event_name = 'add_to_cart' THEN event_timestamp END) AS t_add_to_cart,
    MIN(CASE WHEN event_name = 'begin_checkout' THEN event_timestamp END) AS t_begin_checkout,
    MIN(CASE WHEN event_name = 'purchase' THEN event_timestamp END) AS t_purchase
  FROM session_events
  GROUP BY session_id
),

session_event_times_readable AS (
  SELECT
    session_id,
    t_view_item,
    TIMESTAMP_MICROS(t_view_item) AS t_view_item_ts,
    t_add_to_cart,
    TIMESTAMP_MICROS(t_add_to_cart) AS t_add_to_cart_ts,
    t_begin_checkout,
    TIMESTAMP_MICROS(t_begin_checkout) AS t_begin_checkout_ts,
    t_purchase,
    TIMESTAMP_MICROS(t_purchase) AS t_purchase_ts
  FROM session_event_times
),

-- Count sessions that reached stages regardless of order
session_stage_counts AS (
  SELECT
    COUNT(1) AS total_sessions,
    SUM(CASE WHEN t_view_item IS NOT NULL THEN 1 ELSE 0 END) AS sessions_view_item,
    SUM(CASE WHEN t_add_to_cart IS NOT NULL THEN 1 ELSE 0 END) AS sessions_add_to_cart,
    SUM(CASE WHEN t_begin_checkout IS NOT NULL THEN 1 ELSE 0 END) AS sessions_begin_checkout,
    SUM(CASE WHEN t_purchase IS NOT NULL THEN 1 ELSE 0 END) AS sessions_purchase
  FROM session_event_times
),

-- Count sessions where events occurred in strict ascending order
ordered_sessions AS (
  SELECT
    COUNT(1) AS sessions_in_strict_order
  FROM session_event_times
  WHERE
    t_view_item IS NOT NULL
    AND t_add_to_cart IS NOT NULL
    AND t_begin_checkout IS NOT NULL
    AND t_purchase IS NOT NULL
    AND t_view_item < t_add_to_cart
    AND t_add_to_cart < t_begin_checkout
    AND t_begin_checkout < t_purchase
)

SELECT
  s.total_sessions,
  s.sessions_view_item,
  s.sessions_add_to_cart,
  s.sessions_begin_checkout,
  s.sessions_purchase,
  o.sessions_in_strict_order,
  SAFE_DIVIDE(s.sessions_add_to_cart, NULLIF(s.sessions_view_item,0)) AS convert_view_to_add,
  SAFE_DIVIDE(s.sessions_begin_checkout, NULLIF(s.sessions_add_to_cart,0)) AS convert_add_to_begin_checkout,
  SAFE_DIVIDE(s.sessions_purchase, NULLIF(s.sessions_begin_checkout,0)) AS convert_begin_checkout_to_purchase,
  SAFE_DIVIDE(s.sessions_purchase, NULLIF(s.sessions_view_item,0)) AS overall_convert_view_to_purchase,
  SAFE_DIVIDE(o.sessions_in_strict_order, NULLIF(s.total_sessions,0)) AS pct_sessions_with_full_ordered_funnel
FROM session_stage_counts s
CROSS JOIN ordered_sessions o;

-- Notes:
-- * This query uses TIMESTAMP_MICROS(event_timestamp) for readable timestamps and numeric event_timestamp for comparisons (assumed microseconds).
-- * Sessions without ga_session_id are included with a synthetic id — consider excluding them if you want strictly recorded sessions only.
