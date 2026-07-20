-- 01_data_exploration.sql
-- Purpose: Event-level exploration: list event types, counts, distinct users, and per-table row counts.
-- Unit of analysis: events (use event counts and distinct users where noted).
-- Recommendation: run on a small date window first using _TABLE_SUFFIX to control cost.

-- Parameters (adjust before running):
--   start_date = '20201101'
--   end_date   = '20210131'

-- 1) List event types with total event counts and distinct users (events unit, distinct users reported)
SELECT
  event_name,
  COUNT(1) AS total_events,
  COUNT(DISTINCT user_pseudo_id) AS distinct_users
FROM
  `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE
  _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
GROUP BY
  event_name
ORDER BY
  total_events DESC;

-- 2) Dataset date range and total record count (per-day summary; events unit)
SELECT
  _TABLE_SUFFIX AS table_date,
  COUNT(1) AS rows
FROM
  `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE
  _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
GROUP BY
  table_date
ORDER BY
  table_date;

-- Notes:
-- This file is safe to preview. For heavy aggregation across the whole range, consider
-- running on a smaller date window first to estimate cost.
