-- 09_model_features.sql
-- Purpose: Build session-level modeling features with an explicit prediction moment (observation window) to avoid leakage.
-- Unit of analysis: sessions
-- Target: session_purchase = 1 if a purchase occurs AFTER the observation window and within the label window.

-- IMPORTANT: Run sql/00_schema_inspection.sql first to confirm event_timestamp units and ga_session_id presence.

DECLARE observation_window_seconds INT64 DEFAULT 600; -- e.g., 10 minutes
DECLARE label_window_seconds INT64 DEFAULT 3600; -- e.g., 1 hour (adjust to session semantics)

-- Step 1: Read raw events and extract ga_session_id
WITH raw AS (
  SELECT
    user_pseudo_id,
    event_name,
    event_timestamp,
    TIMESTAMP_MICROS(event_timestamp) AS event_ts,
    event_date,
    device.category AS device_category,
    traffic_source.source AS source,
    traffic_source.medium AS medium,
    geo.country AS country,
    event_params,
    (SELECT COALESCE(CAST(ep.value.int_value AS STRING), ep.value.string_value) FROM UNNEST(event_params) ep WHERE ep.key = 'ga_session_id' LIMIT 1) AS ga_session_id
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),

-- Step 2: Build session start times (session unit)
session_start AS (
  SELECT
    CONCAT(user_pseudo_id, '_', COALESCE(ga_session_id,'unknown')) AS session_id,
    user_pseudo_id,
    MIN(event_timestamp) AS session_start_ts
  FROM raw
  GROUP BY user_pseudo_id, ga_session_id
),

-- Step 3: Join raw events to session starts to compute features relative to session start
events_with_session AS (
  SELECT
    r.*,
    CONCAT(r.user_pseudo_id, '_', COALESCE(r.ga_session_id,'unknown')) AS session_id
  FROM raw r
  JOIN session_start s
    ON s.user_pseudo_id = r.user_pseudo_id
    AND CONCAT(r.user_pseudo_id, '_', COALESCE(r.ga_session_id,'unknown')) = CONCAT(s.user_pseudo_id, '_', COALESCE(session_start.ga_session_id,'unknown'))
),

-- Note: The JOIN above assumes ga_session_id grouping is consistent. If ga_session_id is NULL/absent for many events, consider sessionization via timestamp gap instead.

-- Step 4: Compute observation cutoff and label cutoff in microseconds (GA4 event_timestamp commonly in microseconds). Use TIMESTAMP_MICROS for readability.
obs_and_labels AS (
  SELECT
    s.session_id,
    s.user_pseudo_id,
    s.session_start_ts,
    TIMESTAMP_MICROS(s.session_start_ts) AS session_start_ts_readable,
    s.session_start_ts + observation_window_seconds * 1000000 AS observation_cutoff_ts,
    TIMESTAMP_MICROS(s.session_start_ts + observation_window_seconds * 1000000) AS observation_cutoff_ts_readable,
    s.session_start_ts + label_window_seconds * 1000000 AS label_cutoff_ts,
    TIMESTAMP_MICROS(s.session_start_ts + label_window_seconds * 1000000) AS label_cutoff_ts_readable
  FROM session_start s
),

-- Step 5: Features computed from events that occur ON or BEFORE the observation cutoff (no leakage). Also track if a purchase occurs DURING the observation window (for handling or exclusion in modeling)
features AS (
  SELECT
    o.session_id,
    o.user_pseudo_id,
    ANY_VALUE(r.device_category) AS device_category,
    ANY_VALUE(r.source) AS source,
    ANY_VALUE(r.medium) AS medium,
    ANY_VALUE(r.country) AS country,
    SUM(CASE WHEN r.event_timestamp <= o.observation_cutoff_ts AND r.event_name = 'view_item' THEN 1 ELSE 0 END) AS views_in_obs_window,
    SUM(CASE WHEN r.event_timestamp <= o.observation_cutoff_ts AND r.event_name = 'add_to_cart' THEN 1 ELSE 0 END) AS adds_in_obs_window,
    SUM(CASE WHEN r.event_timestamp <= o.observation_cutoff_ts AND r.event_name = 'begin_checkout' THEN 1 ELSE 0 END) AS begins_in_obs_window,
    COUNT(1) FILTER(WHERE r.event_timestamp <= o.observation_cutoff_ts) AS total_events_in_obs_window,
    -- purchases during the observation window (used to mark sessions where the purchase already occurred)
    MAX(CASE WHEN r.event_timestamp <= o.observation_cutoff_ts AND r.event_name = 'purchase' THEN 1 ELSE 0 END) AS purchase_during_observation
  FROM obs_and_labels o
  LEFT JOIN raw r
    ON CONCAT(r.user_pseudo_id, '_', COALESCE(r.ga_session_id,'unknown')) = o.session_id
  GROUP BY o.session_id, o.user_pseudo_id
),

-- Step 6: Labels: whether a purchase occurs AFTER the observation cutoff and BEFORE or AT the label cutoff
labels AS (
  SELECT
    o.session_id,
    MAX(CASE WHEN r.event_name = 'purchase' AND r.event_timestamp > o.observation_cutoff_ts AND r.event_timestamp <= o.label_cutoff_ts THEN 1 ELSE 0 END) AS purchase_after_obs_within_label
  FROM obs_and_labels o
  LEFT JOIN raw r
    ON CONCAT(r.user_pseudo_id, '_', COALESCE(r.ga_session_id,'unknown')) = o.session_id
  GROUP BY o.session_id
),

-- Step 7: Combine features and labels; document handling of edge cases
final AS (
  SELECT
    f.*,
    COALESCE(l.purchase_after_obs_within_label, 0) AS session_purchase_label
  FROM features f
  LEFT JOIN labels l USING (session_id)
)

SELECT
  session_id,
  user_pseudo_id,
  device_category,
  source,
  medium,
  country,
  views_in_obs_window,
  adds_in_obs_window,
  begins_in_obs_window,
  total_events_in_obs_window,
  purchase_during_observation,
  session_purchase_label
FROM final;

-- Notes (do read before modeling):
-- * Unit: sessions. Each row is one session_id (constructed from user_pseudo_id and ga_session_id).
-- * Purchase during observation window: these sessions may either be excluded from training (if predicting future purchases) or labeled differently depending on your modeling goal. The query reports purchase_during_observation so you can filter or flag them.
-- * Sessions shorter than the observation window: if the session has no events after session_start that reach the observation cutoff, the feature counts will reflect only available events; you may choose to exclude short sessions or handle them via an indicator.
-- * Sessions near the dataset boundary: sessions that start near the dataset end may have incomplete label windows; consider filtering sessions whose label_cutoff_ts exceeds the analysis end date (or only include sessions with label_cutoff_ts <= last_available_event_ts). This query does not automatically filter dataset-boundary sessions — handle that after inspection.
-- * Post-purchase events: features are computed only from events ON or BEFORE the observation cutoff; events after purchase within the observation window are not used as predictors. For sessions with a purchase during observation, purchase_during_observation = 1 and session_purchase_label will typically be 0 because label only counts purchases after observation.
-- * Time units: this query assumes event_timestamp is in microseconds. Confirm with sql/00_schema_inspection.sql and adjust multipliers if needed.
