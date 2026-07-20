-- 07_traffic_source_analysis.sql
-- Purpose: Session-level funnel comparison by traffic source and medium
-- Unit of analysis: sessions
-- NOTE ON ATTRIBUTION: Top-level traffic_source.source and traffic_source.medium in GA4 typically reflect FIRST-USER ACQUISITION (the source/medium that brought the user). Do NOT assume session-level attribution from these fields. Run sql/00_schema_inspection.sql to check for session-level campaign params (e.g., collected_traffic_source or campaign keys in event_params) before interpreting these fields as session attribution.

WITH raw AS (
  SELECT
    user_pseudo_id,
    event_name,
    (SELECT COALESCE(CAST(ep.value.int_value AS STRING), ep.value.string_value) FROM UNNEST(event_params) ep WHERE ep.key = 'ga_session_id' LIMIT 1) AS ga_session_id,
    traffic_source.source AS source,
    traffic_source.medium AS medium
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),

sessions AS (
  SELECT
    CONCAT(user_pseudo_id, '_', COALESCE(ga_session_id, 'unknown')) AS session_id,
    COALESCE(source, '(unknown)') AS source,
    COALESCE(medium, '(unknown)') AS medium,
    user_pseudo_id,
    event_name
  FROM raw
),

session_flags AS (
  SELECT
    session_id,
    source,
    medium,
    ANY_VALUE(user_pseudo_id) AS user_pseudo_id,
    MAX(CASE WHEN event_name = 'view_item' THEN 1 ELSE 0 END) AS viewed_item,
    MAX(CASE WHEN event_name = 'add_to_cart' THEN 1 ELSE 0 END) AS added_to_cart,
    MAX(CASE WHEN event_name = 'begin_checkout' THEN 1 ELSE 0 END) AS began_checkout,
    MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) AS purchased
  FROM sessions
  GROUP BY session_id, source, medium
),

channel_summary AS (
  SELECT
    source,
    medium,
    COUNT(1) AS total_sessions,
    SUM(viewed_item) AS sessions_view_item,
    SUM(added_to_cart) AS sessions_add_to_cart,
    SUM(began_checkout) AS sessions_begin_checkout,
    SUM(purchased) AS sessions_purchase
  FROM session_flags
  GROUP BY source, medium
)

SELECT
  source,
  medium,
  total_sessions,
  sessions_view_item,
  sessions_add_to_cart,
  sessions_begin_checkout,
  sessions_purchase,
  SAFE_DIVIDE(sessions_add_to_cart, NULLIF(sessions_view_item,0)) AS convert_view_to_add,
  SAFE_DIVIDE(sessions_purchase, NULLIF(sessions_view_item,0)) AS overall_convert_view_to_purchase
FROM channel_summary
ORDER BY total_sessions DESC
LIMIT 200;

-- Notes:
-- * Unit: sessions. Confirm whether traffic_source fields represent session attribution in this export. If not, adapt to event- or user-level interpretation and document the choice.
-- * Sessions with source/medium '(unknown)' indicate missing traffic_source values; investigate if these should be excluded.
