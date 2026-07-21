-- GA4 Tracking Health Monitor
-- Detects event-specific tracking outages while accounting for sitewide traffic changes.

WITH date_spine AS (
  SELECT date
  FROM UNNEST(
    GENERATE_DATE_ARRAY(
      DATE '2020-11-01',
      DATE '2021-01-31'
    )
  ) AS date
),

monitored_events AS (
  SELECT event_name
  FROM UNNEST([
    'page_view',
    'view_item',
    'add_to_cart',
    'begin_checkout',
    'purchase'
  ]) AS event_name
),

calendar AS (
  SELECT
    date_spine.date,
    monitored_events.event_name
  FROM date_spine
  CROSS JOIN monitored_events
),

daily_event_counts AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,
    event_name,
    COUNT(*) AS event_count
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
    AND event_name IN (
      'page_view',
      'view_item',
      'add_to_cart',
      'begin_checkout',
      'purchase'
    )
  GROUP BY
    date,
    event_name
),

complete_daily_counts AS (
  SELECT
    calendar.date,
    calendar.event_name,
    COALESCE(daily_event_counts.event_count, 0) AS event_count
  FROM calendar
  LEFT JOIN daily_event_counts
    USING (date, event_name)
),

event_baselines AS (
  SELECT
    date,
    event_name,
    event_count,

    COUNT(*) OVER (
      PARTITION BY event_name
      ORDER BY date
      ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
    ) AS previous_days_available,

    AVG(event_count) OVER (
      PARTITION BY event_name
      ORDER BY date
      ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
    ) AS expected_event_count,

    STDDEV_SAMP(event_count) OVER (
      PARTITION BY event_name
      ORDER BY date
      ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
    ) AS event_count_stddev
  FROM complete_daily_counts
),

event_metrics AS (
  SELECT
    date,
    event_name,
    event_count,
    previous_days_available,

    ROUND(expected_event_count, 2) AS expected_event_count,

    ROUND(
      SAFE_DIVIDE(event_count, expected_event_count),
      3
    ) AS event_volume_ratio,

    ROUND(
      SAFE_DIVIDE(
        event_count - expected_event_count,
        event_count_stddev
      ),
      2
    ) AS event_volume_z_score
  FROM event_baselines
),

page_view_metrics AS (
  SELECT
    date,
    event_count AS page_view_count,
    expected_event_count AS expected_page_view_count,

    ROUND(
      SAFE_DIVIDE(event_count, expected_event_count),
      3
    ) AS page_view_ratio
  FROM event_baselines
  WHERE event_name = 'page_view'
),

tracking_health AS (
  SELECT
    metrics.date,
    metrics.event_name,
    metrics.event_count,
    metrics.expected_event_count,
    metrics.event_volume_ratio,
    metrics.event_volume_z_score,

    page_views.page_view_count,

    ROUND(
      page_views.expected_page_view_count,
      2
    ) AS expected_page_view_count,

    page_views.page_view_ratio,

    ROUND(
      SAFE_DIVIDE(
        metrics.event_volume_ratio,
        page_views.page_view_ratio
      ),
      3
    ) AS traffic_adjusted_event_ratio,

    CASE
      WHEN metrics.previous_days_available < 7
        THEN 'INSUFFICIENT_HISTORY'

      WHEN metrics.event_count = 0
        AND metrics.expected_event_count >= 25
        AND page_views.page_view_ratio >= 0.50
        THEN 'CRITICAL_TRACKING_OUTAGE'

      WHEN metrics.event_volume_z_score <= -3
        AND SAFE_DIVIDE(
          metrics.event_volume_ratio,
          page_views.page_view_ratio
        ) <= 0.50
        THEN 'WARNING_EVENT_DROP'

      WHEN metrics.event_volume_z_score <= -3
        AND SAFE_DIVIDE(
          metrics.event_volume_ratio,
          page_views.page_view_ratio
        ) > 0.50
        THEN 'LIKELY_TRAFFIC_DECLINE'

      ELSE 'NORMAL'
    END AS tracking_status

  FROM event_metrics AS metrics
  LEFT JOIN page_view_metrics AS page_views
    USING (date)

  -- Page views provide traffic context and do not need a separate alert row.
  WHERE metrics.event_name != 'page_view'
)

SELECT
  date,
  event_name,
  event_count,
  expected_event_count,
  event_volume_ratio,
  event_volume_z_score,
  page_view_count,
  expected_page_view_count,
  page_view_ratio,
  traffic_adjusted_event_ratio,
  tracking_status
FROM tracking_health
WHERE tracking_status NOT IN (
  'NORMAL',
  'INSUFFICIENT_HISTORY'
)
ORDER BY
  date,
  event_name;