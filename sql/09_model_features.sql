-- =============================================================================
-- 09_model_features.sql
-- Purpose  : Leakage-safe, session-level feature table for purchase prediction.
-- Dataset  : bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*
-- Dates    : 2020-11-01 through 2021-01-31
-- Unit     : One row per GA4 session that contains at least one view_item event.
-- Session key : CONCAT(user_pseudo_id, '_', ga_session_id)
--              Records with NULL user_pseudo_id or NULL ga_session_id excluded.
-- Prediction moment : Immediately after the session's first view_item event.
-- Target   : purchased_later_in_session = 1 if a purchase event occurs
--            strictly after the first view_item timestamp in the same session.
--            No one-hour or other arbitrary label window is imposed; the
--            session boundary (ga_session_id) naturally limits label scope.
-- Prerequisites : Run sql/00_schema_inspection.sql first to confirm
--                 event_timestamp is in microseconds and ga_session_id is
--                 present in event_params.
-- =============================================================================

-- ── LEAKAGE CONTROLS ──────────────────────────────────────────────────────────
-- 1. All event-count features use event_timestamp < first_view_item_ts (strict
--    less-than). No event at or after the prediction moment contributes to any
--    feature.
-- 2. Item details (first_item_name, first_item_category, first_item_price) come
--    from the view_item event that IS the prediction moment, not from any later
--    event.
-- 3. The following event types are intentionally excluded from all feature
--    aggregations:
--      add_to_cart    — post-prediction-moment funnel step
--      begin_checkout — downstream of add_to_cart, directly precedes purchase
--      purchase       — the outcome; appears only in target construction
--    Revenue, transaction IDs, and ecommerce totals are not selected anywhere.
-- ─────────────────────────────────────────────────────────────────────────────

-- ── STEP 1: Raw event extraction ──────────────────────────────────────────────
-- Reads all events for the analysis period. ga_session_id is stored in
-- event_params as int_value (string_value used as fallback for edge cases).
-- Records with NULL user_pseudo_id are excluded here. Records where
-- ga_session_id cannot be resolved are excluded in Step 2.
-- Note: event_timestamp is in microseconds (confirmed via 00_schema_inspection).
WITH raw AS (
  SELECT
    user_pseudo_id,
    event_name,
    event_timestamp,
    device.category                                               AS device_category,
    geo.country                                                   AS country,
    -- acquisition_source and acquisition_medium reflect FIRST-USER ACQUISITION:
    -- the source/medium that originally brought this user to the store. These
    -- are NOT session-level attribution fields. The same value appears on every
    -- session for a returning user, regardless of how they arrived for this
    -- specific visit. Treat as user-level acquisition cohort signals only.
    traffic_source.source                                         AS acquisition_source,
    traffic_source.medium                                         AS acquisition_medium,
    items,  -- full items array; items[SAFE_OFFSET(0)] used for item features
    COALESCE(
      CAST(
        (SELECT ep.value.int_value
         FROM UNNEST(event_params) ep
         WHERE ep.key = 'ga_session_id'
         LIMIT 1) AS STRING),
      (SELECT ep.value.string_value
       FROM UNNEST(event_params) ep
       WHERE ep.key = 'ga_session_id'
       LIMIT 1)
    )                                                             AS ga_session_id
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
    AND user_pseudo_id IS NOT NULL
),

-- ── STEP 2: Exclude unresolvable session IDs; build composite session key ──────
valid_raw AS (
  SELECT
    CONCAT(user_pseudo_id, '_', ga_session_id)  AS session_id,
    user_pseudo_id,
    ga_session_id,
    event_name,
    event_timestamp,
    device_category,
    country,
    acquisition_source,
    acquisition_medium,
    items
  FROM raw
  WHERE ga_session_id IS NOT NULL
),

-- ── STEP 3: Session anchor — establishes the prediction moment ─────────────────
-- One row per session containing all session-level scalar attributes.
-- Sessions with no view_item event are excluded by the HAVING clause;
-- they are not valid units of observation for this model.
-- ── PREDICTION TIMESTAMP ──────────────────────────────────────────────────────
-- first_view_item_ts is the microsecond timestamp of the earliest view_item
-- event in the session. All feature windows are anchored to this value.
session_anchor AS (
  SELECT
    session_id,
    ANY_VALUE(device_category)    AS device_category,
    ANY_VALUE(country)            AS country,
    ANY_VALUE(acquisition_source) AS acquisition_source,
    ANY_VALUE(acquisition_medium) AS acquisition_medium,
    MIN(event_timestamp)          AS session_start_ts,
    MIN(IF(event_name = 'view_item', event_timestamp, NULL))
                                  AS first_view_item_ts
  FROM valid_raw
  GROUP BY session_id
  HAVING MIN(IF(event_name = 'view_item', event_timestamp, NULL)) IS NOT NULL
),

-- ── STEP 4: Item details from the first view_item event ───────────────────────
-- Item information (name, category, price) is extracted from the view_item
-- event that defines the prediction moment, so it is fully available at that
-- moment and does not leak any subsequent behavior.
-- Assumption: when a single view_item event contains multiple entries in the
-- items array, items[SAFE_OFFSET(0)] (the first element) is used consistently
-- across all sessions. The first item represents the primary product being
-- viewed in Google Merchandise Store GA4 data.
first_view_item_data AS (
  SELECT
    v.session_id,
    ARRAY_AGG(
      STRUCT(v.items AS items_arr)
      ORDER BY v.event_timestamp
      LIMIT 1
    )[SAFE_OFFSET(0)].items_arr  AS first_view_items
  FROM valid_raw v
  WHERE v.event_name = 'view_item'
  GROUP BY v.session_id
),

-- ── STEP 5: Pre-prediction feature aggregation and target construction ─────────
-- ── PRE-PREDICTION FEATURES ───────────────────────────────────────────────────
-- Every event count uses event_timestamp < first_view_item_ts (strict
-- less-than) so no post-prediction-moment event contaminates a feature.
-- ── TARGET CONSTRUCTION ───────────────────────────────────────────────────────
-- purchased_later_in_session uses event_timestamp > first_view_item_ts (strict
-- greater-than). No arbitrary time-window cap is imposed; the session boundary
-- provided by ga_session_id limits the label window naturally.
-- ── LEAKAGE EXCLUSIONS (inline) ───────────────────────────────────────────────
-- add_to_cart, begin_checkout, and purchase are absent from all SUM/MAX
-- expressions below. They appear in the dataset but are excluded to prevent
-- contamination from post-prediction-moment funnel behavior.
event_features AS (
  SELECT
    v.session_id,

    -- Page views before the first product view
    SUM(IF(v.event_name = 'page_view'
           AND v.event_timestamp < s.first_view_item_ts, 1, 0))
      AS page_views_before_first_view,

    -- Scroll events before the first product view
    SUM(IF(v.event_name = 'scroll'
           AND v.event_timestamp < s.first_view_item_ts, 1, 0))
      AS scroll_events_before_first_view,

    -- Site-search events before the first product view.
    -- Both 'search' and 'view_search_results' are counted; GA4 implementations
    -- vary in which event name is used for on-site search interactions.
    SUM(IF(v.event_name IN ('search', 'view_search_results')
           AND v.event_timestamp < s.first_view_item_ts, 1, 0))
      AS search_events_before_first_view,

    -- Promotion impression events before the first product view
    SUM(IF(v.event_name = 'view_promotion'
           AND v.event_timestamp < s.first_view_item_ts, 1, 0))
      AS promotion_views_before_first_view,

    -- GA4 user_engagement pings before the first product view.
    -- The 'user_engagement' event is fired by the Google tag when a page has
    -- been actively in focus for a qualifying duration.
    SUM(IF(v.event_name = 'user_engagement'
           AND v.event_timestamp < s.first_view_item_ts, 1, 0))
      AS engagement_events_before_first_view,

    -- New-visitor flag: 1 if a first_visit event occurred at or before the
    -- first view_item. Uses <= because first_visit can coincide with the
    -- view_item timestamp in very short sessions.
    MAX(IF(v.event_name = 'first_visit'
           AND v.event_timestamp <= s.first_view_item_ts, 1, 0))
      AS is_new_visitor,

    -- ── TARGET ────────────────────────────────────────────────────────────────
    -- 1 if a purchase event occurs strictly after the first view_item timestamp
    -- in this session. 0 otherwise.
    -- LEAKAGE EXCLUSION: purchase is not counted in any feature above.
    MAX(IF(v.event_name = 'purchase'
           AND v.event_timestamp > s.first_view_item_ts, 1, 0))
      AS purchased_later_in_session

  FROM valid_raw v
  JOIN session_anchor s USING (session_id)
  GROUP BY v.session_id
),

-- ── STEP 6: Final assembly ────────────────────────────────────────────────────
final AS (
  SELECT
    -- ── Identifiers and chronological splitting column ─────────────────────────
    s.session_id,
    DATE(TIMESTAMP_MICROS(s.first_view_item_ts))                    AS session_date,
    s.first_view_item_ts                                             AS first_view_item_timestamp,

    -- ── Session-level features (available at session open, before any event) ───
    COALESCE(s.device_category,    'unknown')                        AS device_category,
    COALESCE(s.country,            'unknown')                        AS country,
    -- First-user acquisition fields; see Step 1 comment on attribution scope.
    COALESCE(s.acquisition_source, '(not set)')                      AS acquisition_source,
    COALESCE(s.acquisition_medium, '(not set)')                      AS acquisition_medium,

    -- ── Item features from the first view_item event (prediction moment) ───────
    -- See Step 4 for the items[SAFE_OFFSET(0)] assumption.
    -- first_item_price is left NULL when absent; no meaningful numeric default
    -- exists for price and imputation should be handled in the modeling notebook.
    LOWER(TRIM(COALESCE(
      fi.first_view_items[SAFE_OFFSET(0)].item_name,
      '(unknown)')))                                                  AS first_item_name,
    COALESCE(
      fi.first_view_items[SAFE_OFFSET(0)].item_category,
      '(unknown)')                                                    AS first_item_category,
    fi.first_view_items[SAFE_OFFSET(0)].price                        AS first_item_price,

    -- ── Temporal features derived from the prediction moment timestamp ─────────
    -- DAYOFWEEK: 1 = Sunday, 2 = Monday, ..., 7 = Saturday (BigQuery convention)
    EXTRACT(HOUR      FROM TIMESTAMP_MICROS(s.first_view_item_ts))   AS hour_of_day,
    EXTRACT(DAYOFWEEK FROM TIMESTAMP_MICROS(s.first_view_item_ts))   AS day_of_week,

    -- Seconds elapsed from session start to the first view_item.
    -- 0 is valid (first event in the session was the view_item).
    -- SAFE_DIVIDE returns NULL on divide-by-zero; integer division by 1000000
    -- is safe here but SAFE_DIVIDE preserves type as FLOAT64 for model use.
    SAFE_DIVIDE(
      s.first_view_item_ts - s.session_start_ts,
      1000000)                                                        AS seconds_from_session_start_to_first_view,

    -- ── PRE-PREDICTION event counts ────────────────────────────────────────────
    COALESCE(e.page_views_before_first_view,        0)               AS page_views_before_first_view,
    COALESCE(e.scroll_events_before_first_view,     0)               AS scroll_events_before_first_view,
    COALESCE(e.search_events_before_first_view,     0)               AS search_events_before_first_view,
    COALESCE(e.promotion_views_before_first_view,   0)               AS promotion_views_before_first_view,
    COALESCE(e.engagement_events_before_first_view, 0)               AS engagement_events_before_first_view,
    COALESCE(e.is_new_visitor,                      0)               AS is_new_visitor,

    -- ── Target ────────────────────────────────────────────────────────────────
    COALESCE(e.purchased_later_in_session,          0)               AS purchased_later_in_session

  FROM session_anchor        s
  LEFT JOIN first_view_item_data fi USING (session_id)
  LEFT JOIN event_features       e  USING (session_id)
)

-- Final output: one row per session, ordered chronologically for review.
-- Remove ORDER BY when writing to a destination table to avoid unnecessary sort cost.
SELECT * FROM final
ORDER BY session_date, session_id;


-- =============================================================================
-- VALIDATION QUERIES
-- These are provided as commented SQL to be run separately after the main query
-- above has been saved to a destination table.
-- Replace `your_dataset.model_features` with your actual table reference.
-- All checks below should return the noted expected result before proceeding
-- to the modeling notebook.
-- =============================================================================

-- 1. Total row count (baseline; record for reproducibility)
-- SELECT COUNT(*) AS total_rows
-- FROM your_dataset.model_features;

-- 2. Distinct session IDs (must equal total_rows — confirms one row per session)
-- SELECT COUNT(DISTINCT session_id) AS distinct_sessions
-- FROM your_dataset.model_features;

-- 3. Duplicate session IDs (expected: zero rows returned)
-- SELECT session_id, COUNT(*) AS n
-- FROM your_dataset.model_features
-- GROUP BY session_id
-- HAVING n > 1
-- ORDER BY n DESC;

-- 4. Positive target count and rate
-- (expected: positive_rate roughly consistent with the ~6% overall conversion
-- rate documented in README.md; sessions filtered to view_item-only may differ)
-- SELECT
--   SUM(purchased_later_in_session)                               AS positive_count,
--   COUNT(*)                                                      AS total_rows,
--   SAFE_DIVIDE(SUM(purchased_later_in_session), COUNT(*))        AS positive_rate
-- FROM your_dataset.model_features;

-- 5. Session date range (expected: 2020-11-01 to 2021-01-31)
-- SELECT
--   MIN(session_date) AS earliest_session_date,
--   MAX(session_date) AS latest_session_date
-- FROM your_dataset.model_features;

-- 6. Missing-value counts for key features
-- (sentinel values 'unknown' / '(not set)' / '(unknown)' flag imputed nulls)
-- SELECT
--   COUNTIF(device_category     = 'unknown')   AS missing_device_category,
--   COUNTIF(country             = 'unknown')   AS missing_country,
--   COUNTIF(acquisition_source  = '(not set)') AS missing_acquisition_source,
--   COUNTIF(acquisition_medium  = '(not set)') AS missing_acquisition_medium,
--   COUNTIF(first_item_name     = '(unknown)') AS missing_first_item_name,
--   COUNTIF(first_item_category = '(unknown)') AS missing_first_item_category,
--   COUNTIF(first_item_price    IS NULL)        AS missing_first_item_price,
--   COUNT(*) AS total_rows
-- FROM your_dataset.model_features;

-- 7. Negative seconds_from_session_start_to_first_view (expected: zero rows)
-- A negative value would indicate a view_item timestamp earlier than the
-- session's minimum event_timestamp, which would be a data anomaly.
-- SELECT COUNT(*) AS negative_time_to_first_view
-- FROM your_dataset.model_features
-- WHERE seconds_from_session_start_to_first_view < 0;

-- 8. Target values outside {0, 1} (expected: zero rows)
-- SELECT COUNT(*) AS invalid_target_values
-- FROM your_dataset.model_features
-- WHERE purchased_later_in_session NOT IN (0, 1);
