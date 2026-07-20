-- 06_device_analysis.sql
-- Purpose: Session-level funnel comparison by device category (mobile, desktop, tablet)
-- Unit of analysis: sessions (session-level conversion is primary for website performance analysis)
-- Note: session_id is constructed from ga_session_id in event_params; run sql/00_schema_inspection.sql first to confirm ga_session_id exists and its type.

WITH raw AS (
  SELECT
    user_pseudo_id,
    event_name,
    (SELECT COALESCE(CAST(ep.value.int_value AS STRING), ep.value.string_value) FROM UNNEST(event_params) ep WHERE ep.key = 'ga_session_id' LIMIT 1) AS ga_session_id,
    device.category AS device_category
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),

sessions AS (
  SELECT
    CONCAT(user_pseudo_id, '_', COALESCE(ga_session_id, 'unknown')) AS session_id,
    COALESCE(device_category, '(unknown)') AS device_category,
    user_pseudo_id,
    event_name
  FROM raw
),

session_flags AS (
  SELECT
    session_id,
    device_category,
    ANY_VALUE(user_pseudo_id) AS user_pseudo_id,
    MAX(CASE WHEN event_name = 'view_item' THEN 1 ELSE 0 END) AS viewed_item,
    MAX(CASE WHEN event_name = 'add_to_cart' THEN 1 ELSE 0 END) AS added_to_cart,
    MAX(CASE WHEN event_name = 'begin_checkout' THEN 1 ELSE 0 END) AS began_checkout,
    MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) AS purchased
  FROM sessions
  GROUP BY session_id, device_category
),

device_summary AS (
  SELECT
    device_category,
    COUNT(1) AS total_sessions,
    SUM(viewed_item) AS sessions_view_item,
    SUM(added_to_cart) AS sessions_add_to_cart,
    SUM(began_checkout) AS sessions_begin_checkout,
    SUM(purchased) AS sessions_purchase
  FROM session_flags
  GROUP BY device_category
)

SELECT
  device_category,
  total_sessions,
  sessions_view_item,
  sessions_add_to_cart,
  sessions_begin_checkout,
  sessions_purchase,
  SAFE_DIVIDE(sessions_add_to_cart, NULLIF(sessions_view_item,0)) AS convert_view_to_add,
  SAFE_DIVIDE(sessions_begin_checkout, NULLIF(sessions_add_to_cart,0)) AS convert_add_to_begin_checkout,
  SAFE_DIVIDE(sessions_purchase, NULLIF(sessions_begin_checkout,0)) AS convert_begin_checkout_to_purchase,
  SAFE_DIVIDE(sessions_purchase, NULLIF(sessions_view_item,0)) AS overall_convert_view_to_purchase
FROM device_summary
ORDER BY total_sessions DESC;

-- Notes:
-- * Unit of analysis: sessions. Interpret results accordingly (sessions that reached a stage at least once).
-- * Sessions labeled 'unknown' did not have ga_session_id present; consider filtering if you want only recorded sessions.
