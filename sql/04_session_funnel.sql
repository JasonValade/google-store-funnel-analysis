-- 04_session_funnel.sql
-- Purpose: Session-level funnel using ga_session_id extracted from event_params.
-- Creates session_id by combining user_pseudo_id and ga_session_id. Sessions without ga_session_id are labeled '(unknown_session)'.
-- Use _TABLE_SUFFIX to restrict dates.

WITH raw AS (
  SELECT
    user_pseudo_id,
    event_name,
    event_timestamp,
    event_date,
    event_params,
    -- Extract ga_session_id from event_params when present (int_value or string_value)
    (SELECT
       COALESCE(CAST(ep.value.int_value AS STRING), ep.value.string_value)
     FROM UNNEST(event_params) ep
     WHERE ep.key = 'ga_session_id'
     LIMIT 1) AS ga_session_id
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),

sessions AS (
  SELECT
    user_pseudo_id,
    COALESCE(ga_session_id, '(unknown)') AS ga_session_id,
    CONCAT(user_pseudo_id, '_', COALESCE(ga_session_id, 'unknown')) AS session_id,
    event_name
  FROM raw
),

session_flags AS (
  SELECT
    session_id,
    ANY_VALUE(user_pseudo_id) AS user_pseudo_id,
    MAX(CASE WHEN event_name = 'view_item' THEN 1 ELSE 0 END) AS viewed_item,
    MAX(CASE WHEN event_name = 'add_to_cart' THEN 1 ELSE 0 END) AS added_to_cart,
    MAX(CASE WHEN event_name = 'begin_checkout' THEN 1 ELSE 0 END) AS began_checkout,
    MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) AS purchased
  FROM sessions
  GROUP BY session_id
),

summary AS (
  SELECT
    COUNT(1) AS total_sessions,
    SUM(viewed_item) AS sessions_view_item,
    SUM(added_to_cart) AS sessions_add_to_cart,
    SUM(began_checkout) AS sessions_begin_checkout,
    SUM(purchased) AS sessions_purchase
  FROM session_flags
)

SELECT
  total_sessions,
  sessions_view_item,
  sessions_add_to_cart,
  sessions_begin_checkout,
  sessions_purchase,
  SAFE_DIVIDE(sessions_add_to_cart, NULLIF(sessions_view_item,0)) AS convert_view_to_add,
  SAFE_DIVIDE(sessions_begin_checkout, NULLIF(sessions_add_to_cart,0)) AS convert_add_to_begin_checkout,
  SAFE_DIVIDE(sessions_purchase, NULLIF(sessions_begin_checkout,0)) AS convert_begin_checkout_to_purchase,
  SAFE_DIVIDE(sessions_purchase, NULLIF(sessions_view_item,0)) AS overall_convert_view_to_purchase
FROM summary;

-- Notes:
-- * ga_session_id extraction depends on the event_params keys available in your export. Run 00_schema_inspection.sql to confirm the key and value type.
-- * Sessions labeled '(unknown)' may represent events where a session id was not recorded in event_params. Consider filtering or sessionizing via event_timestamp heuristics if needed.
