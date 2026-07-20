-- 00_schema_inspection.sql
-- Purpose: Inspect schema, event_param keys, item fields, and timestamp units in the GA4 export.
-- Unit of analysis for these checks: events (sample rows and metadata). Run on a small date window for quick feedback.
-- Adjust _TABLE_SUFFIX before running. Recommended small-window example: BETWEEN '20201101' AND '20201107'.
-- IMPORTANT: Run each numbered query below separately in the BigQuery console. Do NOT paste the entire file as a single multi-statement job unless your environment supports it — run 1), then 2), then 3), etc., to inspect outputs sequentially.

-- 1) Try INFORMATION_SCHEMA to list columns (may be restricted in public dataset views). If not permitted, skip to the event preview queries below.
SELECT table_name, column_name, data_type
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name LIKE 'events_%'
ORDER BY table_name, ordinal_position
LIMIT 1000;

-- 2) Distinct event names and counts (events unit)
SELECT
  event_name,
  COUNT(1) AS total_events
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20201107'
GROUP BY event_name
ORDER BY total_events DESC;

-- 3) Distinct event_param keys and approximate counts (events unit)
SELECT
  ep.key AS event_param_key,
  COUNT(1) AS cnt
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
  UNNEST(event_params) ep
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20201107'
GROUP BY event_param_key
ORDER BY cnt DESC
LIMIT 500;

-- 4) Sample item JSON (inspect item fields such as item_id, item_name, price, quantity, item_revenue)
SELECT
  event_name,
  TO_JSON_STRING(item) AS item_json
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
  UNNEST(items) AS item
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20201107'
LIMIT 200;

-- 5) Check for common revenue fields on purchase events and whether item_revenue exists
SELECT
  ep.key AS key_name,
  COUNT(1) AS cnt,
  ARRAY_AGG(DISTINCT ep.value.string_value IGNORE NULLS LIMIT 5) AS sample_string_values,
  ARRAY_AGG(DISTINCT ep.value.int_value IGNORE NULLS LIMIT 5) AS sample_int_values,
  ARRAY_AGG(DISTINCT ep.value.double_value IGNORE NULLS LIMIT 5) AS sample_double_values
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
  UNNEST(event_params) ep
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20201107'
  AND (ep.key IN ('value','purchase_revenue','transaction_revenue','item_revenue') OR ep.key LIKE '%revenue%')
GROUP BY key_name
ORDER BY cnt DESC
LIMIT 100;

-- 6) Check presence of ga_session_id (session identifier) and sample types
SELECT
  COUNT(1) AS events_with_ga_session_id,
  COUNT(DISTINCT COALESCE(CAST(ep.value.int_value AS STRING), ep.value.string_value)) AS distinct_ga_session_ids
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
  UNNEST(event_params) ep
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20201107'
  AND ep.key = 'ga_session_id'
  AND (ep.value.int_value IS NOT NULL OR ep.value.string_value IS NOT NULL);

-- 7) Sample event_timestamp values in readable form (events unit)
-- Run separately to inspect typical timestamp values and confirm time units. This simple ordered sample avoids grouping by unique timestamps.
SELECT
  event_timestamp,
  TIMESTAMP_MICROS(event_timestamp) AS event_ts_readable
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20201107'
ORDER BY event_timestamp DESC
LIMIT 50;

-- Guidance:
-- * Use these outputs to decide which revenue fields to use (prefer item.item_revenue or transaction-level keys if present).
-- * Confirm ga_session_id presence and type; if absent, sessionization will require a timestamp-gap approach.
-- * Confirm event_timestamp units (this query uses TIMESTAMP_MICROS to display readable time). If values look incorrect, adjust accordingly.
-- * After confirming schema, run the ordered session and funnel queries which rely on ga_session_id and timestamps.
