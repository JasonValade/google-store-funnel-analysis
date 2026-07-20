-- Product performance and opportunity analysis
-- Product names are normalized because item IDs were inconsistent across
-- view_item and purchase events in the obfuscated dataset.

WITH item_events AS (
  SELECT
    user_pseudo_id,

    (
      SELECT value.int_value
      FROM UNNEST(event_params)
      WHERE key = 'ga_session_id'
    ) AS ga_session_id,

    event_name,
    LOWER(TRIM(item.item_name)) AS product_name,
    item.quantity,
    item.price,
    item.item_revenue

  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
    UNNEST(items) AS item

  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
    AND event_name IN ('view_item', 'purchase')
    AND item.item_name IS NOT NULL
),

product_metrics AS (
  SELECT
    product_name,

    COUNT(
      DISTINCT IF(
        event_name = 'view_item',
        CONCAT(
          user_pseudo_id,
          '-',
          CAST(ga_session_id AS STRING)
        ),
        NULL
      )
    ) AS product_view_sessions,

    COUNT(
      DISTINCT IF(
        event_name = 'purchase',
        CONCAT(
          user_pseudo_id,
          '-',
          CAST(ga_session_id AS STRING)
        ),
        NULL
      )
    ) AS purchase_sessions,

    SUM(
      IF(
        event_name = 'purchase',
        COALESCE(quantity, 1),
        0
      )
    ) AS units_purchased,

    ROUND(
      SUM(
        IF(
          event_name = 'purchase',
          COALESCE(
            item_revenue,
            price * COALESCE(quantity, 1),
            0
          ),
          0
        )
      ),
      2
    ) AS item_revenue

  FROM item_events
  WHERE ga_session_id IS NOT NULL
  GROUP BY product_name
),

calculated_metrics AS (
  SELECT
    product_name,
    product_view_sessions,
    purchase_sessions,
    units_purchased,
    item_revenue,

    ROUND(
      100 * SAFE_DIVIDE(
        purchase_sessions,
        product_view_sessions
      ),
      2
    ) AS product_purchase_rate,

    CASE
      WHEN purchase_sessions = 0
        THEN 'Investigate availability or tracking'
      WHEN SAFE_DIVIDE(
        purchase_sessions,
        product_view_sessions
      ) < 0.01
        THEN 'High-traffic, low-conversion candidate'
      ELSE 'Monitor'
    END AS opportunity_status

  FROM product_metrics
),

revenue_ranking AS (
  SELECT
    'Product Revenue Ranking' AS analysis_type,

    ROW_NUMBER() OVER (
      ORDER BY item_revenue DESC
    ) AS ranking_position,

    product_name,
    product_view_sessions,
    purchase_sessions,
    units_purchased,
    item_revenue,
    product_purchase_rate,
    opportunity_status

  FROM calculated_metrics
),

opportunity_ranking AS (
  SELECT
    'Product Opportunity Ranking' AS analysis_type,

    ROW_NUMBER() OVER (
      ORDER BY
        product_purchase_rate ASC,
        product_view_sessions DESC
    ) AS ranking_position,

    product_name,
    product_view_sessions,
    purchase_sessions,
    units_purchased,
    item_revenue,
    product_purchase_rate,
    opportunity_status

  FROM calculated_metrics

  WHERE product_view_sessions >= 1000
)

SELECT *
FROM revenue_ranking
WHERE ranking_position <= 50

UNION ALL

SELECT *
FROM opportunity_ranking
WHERE ranking_position <= 20

ORDER BY
  analysis_type,
  ranking_position;