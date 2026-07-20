-- 02_data_quality.sql
-- Purpose: Check missing values and common data-quality issues in the GA4 export
-- Adjust _TABLE_SUFFIX range before running to control cost

-- Parameters: start_date/end_date as in other files

WITH sample AS (
  SELECT *
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
)

-- 1) Null checks for top-level fields
SELECT
  COUNT(1) AS total_rows,
  SUM(CASE WHEN user_pseudo_id IS NULL THEN 1 ELSE 0 END) AS null_user_pseudo_id,
  SUM(CASE WHEN event_name IS NULL THEN 1 ELSE 0 END) AS null_event_name,
  SUM(CASE WHEN event_timestamp IS NULL THEN 1 ELSE 0 END) AS null_event_timestamp,
  SUM(CASE WHEN event_date IS NULL THEN 1 ELSE 0 END) AS null_event_date
FROM sample;

-- 2) Check nested fields commonly used (traffic_source, device)
SELECT
  COUNT(1) AS total_rows,
  SUM(CASE WHEN traffic_source.source IS NULL THEN 1 ELSE 0 END) AS null_source,
  SUM(CASE WHEN traffic_source.medium IS NULL THEN 1 ELSE 0 END) AS null_medium,
  SUM(CASE WHEN device.category IS NULL THEN 1 ELSE 0 END) AS null_device_category
FROM sample;

-- 3) Check item-level nesting and presence
SELECT
  COUNT(1) AS total_event_rows,
  SUM(CASE WHEN ARRAY_LENGTH(items) = 0 OR items IS NULL THEN 1 ELSE 0 END) AS events_without_items
FROM sample;

-- 4) Example of extracting a commonly-used event_param (engagement_time_msec)
-- Note: event_params is an array of records; use SAFE extraction patterns
SELECT
  COUNT(1) AS rows_with_engagement_time_msec
FROM sample
WHERE EXISTS (
  SELECT 1 FROM UNNEST(event_params) ep WHERE ep.key = 'engagement_time_msec' AND (ep.value.int_value IS NOT NULL OR ep.value.double_value IS NOT NULL)
);

-- 5) Small preview of item structure (run with LIMIT to inspect schema values)
SELECT
  event_name,
  items
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20201107'
LIMIT 50;

-- Recommendation: Inspect outputs and adapt subsequent queries if field names differ in your environment.
