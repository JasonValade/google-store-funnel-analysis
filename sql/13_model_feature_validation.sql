-- =============================================================================
-- 13_model_feature_validation.sql
-- Purpose  : Materialize the leakage-safe feature table into a BigQuery
--            temporary table and run structured validation checks against it.
-- Source   : Feature logic is copied verbatim from sql/09_model_features.sql.
--            Do not modify feature definitions or target logic here; any
--            change to feature logic must be made in 09_model_features.sql
--            and then synchronized to this file.
-- Usage    : Run this entire script in one BigQuery job. The TEMP TABLE is
--            scoped to the session and dropped automatically on completion.
--            No permanent table is created.
-- Prerequisites : Run sql/00_schema_inspection.sql first to confirm
--                 event_timestamp is in microseconds and ga_session_id is
--                 present in event_params.
-- =============================================================================

-- =============================================================================
-- SECTION 1: Materialize features into a session-scoped temporary table
-- =============================================================================
-- The feature logic below is an exact copy of sql/09_model_features.sql.
-- The ORDER BY from the SELECT at the end of that script is omitted here
-- because ordering adds cost and is unnecessary for a destination table.
-- =============================================================================

CREATE TEMP TABLE model_features AS (

  -- ── STEP 1: Raw event extraction ────────────────────────────────────────────
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

  -- ── STEP 2: Exclude unresolvable session IDs; build composite session key ────
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

  -- ── STEP 3: Session anchor — establishes the prediction moment ───────────────
  -- One row per session containing all session-level scalar attributes.
  -- Sessions with no view_item event are excluded by the HAVING clause;
  -- they are not valid units of observation for this model.
  -- ── PREDICTION TIMESTAMP ────────────────────────────────────────────────────
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

  -- ── STEP 4: Item details from the first view_item event ─────────────────────
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

  -- ── STEP 5: Pre-prediction feature aggregation and target construction ───────
  -- ── PRE-PREDICTION FEATURES ─────────────────────────────────────────────────
  -- Every event count uses event_timestamp < first_view_item_ts (strict
  -- less-than) so no post-prediction-moment event contaminates a feature.
  -- ── TARGET CONSTRUCTION ─────────────────────────────────────────────────────
  -- purchased_later_in_session uses event_timestamp > first_view_item_ts (strict
  -- greater-than). No arbitrary time-window cap is imposed; the session boundary
  -- provided by ga_session_id limits the label window naturally.
  -- ── LEAKAGE EXCLUSIONS (inline) ─────────────────────────────────────────────
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

      -- ── TARGET ──────────────────────────────────────────────────────────────
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

  -- ── STEP 6: Final assembly ──────────────────────────────────────────────────
  final AS (
    SELECT
      -- ── Identifiers and chronological splitting column ───────────────────────
      s.session_id,
      DATE(TIMESTAMP_MICROS(s.first_view_item_ts))                    AS session_date,
      s.first_view_item_ts                                             AS first_view_item_timestamp,

      -- ── Session-level features (available at session open, before any event) ─
      COALESCE(s.device_category,    'unknown')                        AS device_category,
      COALESCE(s.country,            'unknown')                        AS country,
      -- First-user acquisition fields; see Step 1 comment on attribution scope.
      COALESCE(s.acquisition_source, '(not set)')                      AS acquisition_source,
      COALESCE(s.acquisition_medium, '(not set)')                      AS acquisition_medium,

      -- ── Item features from the first view_item event (prediction moment) ─────
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

      -- ── Temporal features derived from the prediction moment timestamp ────────
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

      -- ── PRE-PREDICTION event counts ──────────────────────────────────────────
      COALESCE(e.page_views_before_first_view,        0)               AS page_views_before_first_view,
      COALESCE(e.scroll_events_before_first_view,     0)               AS scroll_events_before_first_view,
      COALESCE(e.search_events_before_first_view,     0)               AS search_events_before_first_view,
      COALESCE(e.promotion_views_before_first_view,   0)               AS promotion_views_before_first_view,
      COALESCE(e.engagement_events_before_first_view, 0)               AS engagement_events_before_first_view,
      COALESCE(e.is_new_visitor,                      0)               AS is_new_visitor,

      -- ── Target ──────────────────────────────────────────────────────────────
      COALESCE(e.purchased_later_in_session,          0)               AS purchased_later_in_session

    FROM session_anchor        s
    LEFT JOIN first_view_item_data fi USING (session_id)
    LEFT JOIN event_features       e  USING (session_id)
  )

  SELECT * FROM final

); -- end CREATE TEMP TABLE


-- =============================================================================
-- SECTION 2: Overall validation summary
-- =============================================================================
-- Expected conditions:
--   total_rows          = distinct_session_ids  (one row per session)
--   duplicate_session_rows = 0                  (no fanout from any join)
--   invalid_target_values  = 0                  (target is strictly 0 or 1)
--   negative_time_rows     = 0                  (view_item cannot precede the
--                                                session's minimum timestamp)
--   minimum_session_date   = 2020-11-01
--   maximum_session_date   = 2021-01-31
--   purchase_rate_percent is informational; it reflects view_item sessions only
--   and will differ from the 6.05% overall ordered-funnel rate in README.md,
--   which was calculated over all sessions. Both values can be correct.
-- =============================================================================

SELECT
  COUNT(*)                                                AS total_rows,
  COUNT(DISTINCT session_id)                              AS distinct_session_ids,
  -- Expected: 0. Any value > 0 means the feature query produced duplicate rows
  -- for at least one session, indicating a fanout in a join or GROUP BY bug.
  COUNT(*) - COUNT(DISTINCT session_id)                   AS duplicate_session_rows,
  SUM(purchased_later_in_session)                         AS positive_targets,
  SUM(1 - purchased_later_in_session)                     AS negative_targets,
  -- purchase_rate_percent: informational. Not required to equal a predetermined
  -- value; the view_item-filtered population differs from the full-session funnel.
  ROUND(
    100.0 * SAFE_DIVIDE(
      SUM(purchased_later_in_session),
      COUNT(*)),
    2)                                                    AS purchase_rate_percent,
  MIN(session_date)                                       AS minimum_session_date,
  MAX(session_date)                                       AS maximum_session_date,
  -- Expected: 0. purchased_later_in_session should only ever be 0 or 1 because
  -- it is produced by MAX(IF(..., 1, 0)) with COALESCE(..., 0).
  COUNTIF(purchased_later_in_session NOT IN (0, 1))       AS invalid_target_values,
  -- Expected: 0. A negative value means a view_item event has a timestamp
  -- earlier than MIN(event_timestamp) for that session, which is a data anomaly.
  -- SAFE_DIVIDE returns NULL when the denominator is zero; those rows are
  -- excluded from the < 0 comparison and will not inflate this count.
  COUNTIF(seconds_from_session_start_to_first_view < 0)   AS negative_time_rows
FROM model_features;


-- =============================================================================
-- SECTION 3: Missing-value summary
-- =============================================================================
-- SQL NULL counts reflect fields that were NULL before COALESCE was applied but
-- could not be resolved. After the COALESCE in the feature query, categorical
-- columns will not contain SQL NULLs; their missing-value signal is instead
-- encoded as sentinel strings ('unknown', '(not set)', '(unknown)').
--
-- This query therefore reports two distinct counts per categorical column:
--   missing_*  = SQL NULL remaining after COALESCE (should be 0 for all
--                columns that have COALESCE applied in the feature query)
--   unknown_*  = rows where the sentinel value was substituted, indicating the
--                original source field was NULL or absent
--
-- first_item_price has no COALESCE sentinel; its missing count is a true NULL.
-- first_view_item_timestamp cannot be NULL (the HAVING clause in session_anchor
-- guarantees it), so its missing count should be 0.
-- =============================================================================

SELECT
  -- ── SQL NULL counts (should all be 0 for COALESCE-covered columns) ───────────
  COUNTIF(device_category             IS NULL)  AS missing_device_category,
  COUNTIF(country                     IS NULL)  AS missing_country,
  COUNTIF(acquisition_source          IS NULL)  AS missing_acquisition_source,
  COUNTIF(acquisition_medium          IS NULL)  AS missing_acquisition_medium,
  COUNTIF(first_item_name             IS NULL)  AS missing_first_item_name,
  COUNTIF(first_item_category         IS NULL)  AS missing_first_item_category,
  -- first_item_price is intentionally left NULL when absent (no sentinel).
  -- Imputation is deferred to the modeling notebook.
  COUNTIF(first_item_price            IS NULL)  AS missing_first_item_price,
  -- first_view_item_timestamp must never be NULL; HAVING in session_anchor
  -- enforces this. Any non-zero value here signals a query logic regression.
  COUNTIF(first_view_item_timestamp   IS NULL)  AS missing_first_view_timestamp,

  -- ── Sentinel-value counts (original field was NULL; COALESCE substituted) ────
  COUNTIF(device_category     = 'unknown')      AS unknown_device_category,
  COUNTIF(country             = 'unknown')      AS unknown_country,
  COUNTIF(acquisition_source  = '(not set)')    AS unknown_acquisition_source,
  COUNTIF(acquisition_medium  = '(not set)')    AS unknown_acquisition_medium,
  COUNTIF(first_item_name     = '(unknown)')    AS unknown_first_item_name,
  COUNTIF(first_item_category = '(unknown)')    AS unknown_first_item_category

FROM model_features;


-- =============================================================================
-- SECTION 4: Target distribution
-- =============================================================================
-- Shows the count and percentage of sessions in each target class.
-- purchased_later_in_session = 1 represents purchasing sessions;
-- purchased_later_in_session = 0 represents non-purchasing sessions.
-- The percentage is computed relative to the total row count; SAFE_DIVIDE
-- guards against division by zero if the table is unexpectedly empty.
-- =============================================================================

SELECT
  purchased_later_in_session                            AS target_value,
  COUNT(*)                                              AS session_count,
  ROUND(
    100.0 * SAFE_DIVIDE(COUNT(*), SUM(COUNT(*)) OVER()),
    2)                                                  AS pct_of_all_sessions
FROM model_features
GROUP BY purchased_later_in_session
ORDER BY purchased_later_in_session;


-- =============================================================================
-- SECTION 5: Monthly distribution
-- =============================================================================
-- Aggregates sessions by calendar month to verify coverage across the full
-- analysis window (2020-11 through 2021-01) and to surface any month with an
-- anomalous purchase rate that may warrant investigation before modeling.
-- DATE_TRUNC truncates session_date to the first day of each month.
-- =============================================================================

SELECT
  DATE_TRUNC(session_date, MONTH)                       AS month,
  COUNT(*)                                              AS total_sessions,
  SUM(purchased_later_in_session)                       AS purchasing_sessions,
  ROUND(
    100.0 * SAFE_DIVIDE(
      SUM(purchased_later_in_session),
      COUNT(*)),
    2)                                                  AS purchase_rate_percent
FROM model_features
GROUP BY month
ORDER BY month;


-- =============================================================================
-- SECTION 6: Numerical feature range checks (long format)
-- =============================================================================
-- Returns one row per numerical feature showing its observed minimum, maximum,
-- average, and NULL count. The long format keeps output compact regardless of
-- how many features are checked.
--
-- Expected conditions per feature:
--   first_item_price
--     min >= 0 (prices should be non-negative; 0 may appear for free items)
--     null_count > 0 is expected (price is intentionally left NULL when absent)
--
--   seconds_from_session_start_to_first_view
--     min >= 0 (view_item cannot precede session start; confirmed by Section 2)
--     null_count = 0 expected (SAFE_DIVIDE produces NULL only on zero divisor,
--     which cannot occur because event_timestamp is always a positive integer)
--
--   page_views_before_first_view
--   scroll_events_before_first_view
--   search_events_before_first_view
--   promotion_views_before_first_view
--   engagement_events_before_first_view
--     min = 0 (COALESCE ensures no NULLs; 0 is the floor for all count features)
--     null_count = 0 (COALESCE(..., 0) applied in the feature query)
-- =============================================================================

SELECT 'first_item_price'                             AS feature_name,
  MIN(first_item_price)                               AS minimum,
  MAX(first_item_price)                               AS maximum,
  ROUND(AVG(first_item_price), 4)                     AS average,
  COUNTIF(first_item_price IS NULL)                   AS null_count
FROM model_features

UNION ALL

SELECT 'seconds_from_session_start_to_first_view'     AS feature_name,
  MIN(seconds_from_session_start_to_first_view)       AS minimum,
  MAX(seconds_from_session_start_to_first_view)       AS maximum,
  ROUND(AVG(seconds_from_session_start_to_first_view), 4) AS average,
  COUNTIF(seconds_from_session_start_to_first_view IS NULL) AS null_count
FROM model_features

UNION ALL

SELECT 'page_views_before_first_view'                 AS feature_name,
  MIN(page_views_before_first_view)                   AS minimum,
  MAX(page_views_before_first_view)                   AS maximum,
  ROUND(AVG(page_views_before_first_view), 4)         AS average,
  COUNTIF(page_views_before_first_view IS NULL)       AS null_count
FROM model_features

UNION ALL

SELECT 'scroll_events_before_first_view'              AS feature_name,
  MIN(scroll_events_before_first_view)                AS minimum,
  MAX(scroll_events_before_first_view)                AS maximum,
  ROUND(AVG(scroll_events_before_first_view), 4)      AS average,
  COUNTIF(scroll_events_before_first_view IS NULL)    AS null_count
FROM model_features

UNION ALL

SELECT 'search_events_before_first_view'              AS feature_name,
  MIN(search_events_before_first_view)                AS minimum,
  MAX(search_events_before_first_view)                AS maximum,
  ROUND(AVG(search_events_before_first_view), 4)      AS average,
  COUNTIF(search_events_before_first_view IS NULL)    AS null_count
FROM model_features

UNION ALL

SELECT 'promotion_views_before_first_view'            AS feature_name,
  MIN(promotion_views_before_first_view)              AS minimum,
  MAX(promotion_views_before_first_view)              AS maximum,
  ROUND(AVG(promotion_views_before_first_view), 4)    AS average,
  COUNTIF(promotion_views_before_first_view IS NULL)  AS null_count
FROM model_features

UNION ALL

SELECT 'engagement_events_before_first_view'          AS feature_name,
  MIN(engagement_events_before_first_view)            AS minimum,
  MAX(engagement_events_before_first_view)            AS maximum,
  ROUND(AVG(engagement_events_before_first_view), 4)  AS average,
  COUNTIF(engagement_events_before_first_view IS NULL) AS null_count
FROM model_features

ORDER BY feature_name;
