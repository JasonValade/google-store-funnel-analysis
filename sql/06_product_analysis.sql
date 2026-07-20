-- 06_product_analysis.sql
-- Purpose: Analyze product views, add-to-cart, purchases, and revenue.
-- Uses UNNEST(items) to aggregate at the product level.
-- Adjust _TABLE_SUFFIX range before running.

WITH events AS (
  SELECT
    event_name,
    user_pseudo_id,
    event_timestamp,
    items,
    event_params
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),

-- Explode items for item-level counts
items_exploded AS (
  SELECT
    event_name,
    user_pseudo_id,
    (SELECT value.string_value FROM UNNEST(items) i WHERE TRUE LIMIT 0) AS _dummy -- placeholder to show items structure
  FROM events
  LIMIT 1
),

-- Proper item-level aggregation example
product_events AS (
  SELECT
    COALESCE(item.item_id, item.item_name) AS product_key,
    item.item_name AS product_name,
    IFNULL(item.price, 0) AS price,
    event_name,
    user_pseudo_id,
    -- example quantity, may be NULL in the obfuscated dataset
    IFNULL(item.quantity, 1) AS quantity,
    -- extract revenue from event_params for purchases when available
    (SELECT
       COALESCE(ep.value.double_value, SAFE_CAST(ep.value.int_value AS FLOAT64))
     FROM UNNEST(event_params) ep
     WHERE ep.key IN ('value','purchase_revenue','price')
     LIMIT 1
    ) AS extracted_value
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`, UNNEST(items) AS item
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),

product_agg AS (
  SELECT
    product_key,
    product_name,
    COUNTIF(event_name = 'view_item') AS view_events,
    COUNT(DISTINCT IF(event_name = 'view_item', user_pseudo_id, NULL)) AS users_viewed,
    COUNTIF(event_name = 'add_to_cart') AS add_to_cart_events,
    COUNT(DISTINCT IF(event_name = 'add_to_cart', user_pseudo_id, NULL)) AS users_added_to_cart,
    COUNTIF(event_name = 'purchase') AS purchase_events,
    COUNT(DISTINCT IF(event_name = 'purchase', user_pseudo_id, NULL)) AS users_purchased,
    SUM(COALESCE(extracted_value, 0) * quantity) AS revenue_estimate
  FROM product_events
  GROUP BY product_key, product_name
)

SELECT
  product_key,
  product_name,
  view_events,
  users_viewed,
  add_to_cart_events,
  users_added_to_cart,
  purchase_events,
  users_purchased,
  revenue_estimate,
  SAFE_DIVIDE(users_purchased, users_viewed) AS view_to_purchase_rate,
  SAFE_DIVIDE(users_added_to_cart, users_viewed) AS view_to_add_rate
FROM product_agg
ORDER BY users_viewed DESC
LIMIT 500;

-- Notes:
-- * The obfuscated sample may not populate all item fields; inspect items in 02_data_quality
-- * extracted_value attempts several keys. Adjust as needed to align with your dataset's purchase revenue field
-- * Identify products with high views but low view_to_purchase_rate as opportunity candidates
