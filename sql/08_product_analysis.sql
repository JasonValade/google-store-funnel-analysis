-- 08_product_analysis.sql
-- Purpose: Product-level analysis for item views, add-to-cart, purchases, and revenue.
-- Unit of analysis: items (UNNEST(items) produces one row per item per event).
-- Revenue policy: prefer item.item_revenue when available. If not present, fall back to item.price * item.quantity. Do NOT mix item-level and transaction-level revenue in the same metric.

-- IMPORTANT: Run sql/00_schema_inspection.sql first to confirm item fields (item_revenue, price, quantity) and to identify transaction-level revenue fields if you need those separately.

WITH item_events AS (
  SELECT
    event_name,
    user_pseudo_id,
    TIMESTAMP_MICROS(event_timestamp) AS event_ts,
    item,
    COALESCE(item.item_id, item.item_name) AS product_key,
    item.item_name AS product_name,
    -- Prefer explicit item_revenue if available (may be in item.item_revenue), otherwise NULL
    SAFE_CAST(item.item_revenue AS FLOAT64) AS item_revenue_field,
    SAFE_CAST(item.price AS FLOAT64) AS item_price,
    SAFE_CAST(item.quantity AS INT64) AS item_quantity
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
    UNNEST(items) AS item
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),

product_agg AS (
  SELECT
    product_key,
    product_name,
    COUNTIF(event_name = 'view_item') AS view_item_rows,
    COUNT(DISTINCT IF(event_name = 'view_item', user_pseudo_id, NULL)) AS users_viewed,
    COUNTIF(event_name = 'add_to_cart') AS add_to_cart_rows,
    COUNT(DISTINCT IF(event_name = 'add_to_cart', user_pseudo_id, NULL)) AS users_added_to_cart,
    COUNTIF(event_name = 'purchase') AS purchase_item_rows,
    COUNT(DISTINCT IF(event_name = 'purchase', user_pseudo_id, NULL)) AS users_purchased,
    -- item-level revenue: prefer item_revenue_field; fallback to item_price * item_quantity when item_revenue_field is NULL
    SUM(CASE WHEN event_name = 'purchase' THEN COALESCE(item_revenue_field, item_price * IFNULL(item_quantity,1)) ELSE 0 END) AS item_revenue_sum
  FROM item_events
  GROUP BY product_key, product_name
)

SELECT
  product_key,
  product_name,
  view_item_rows,
  users_viewed,
  add_to_cart_rows,
  users_added_to_cart,
  purchase_item_rows,
  users_purchased,
  item_revenue_sum,
  SAFE_DIVIDE(users_purchased, NULLIF(users_viewed,0)) AS view_to_purchase_rate,
  SAFE_DIVIDE(users_added_to_cart, NULLIF(users_viewed,0)) AS view_to_add_rate
FROM product_agg
ORDER BY users_viewed DESC
LIMIT 500;

-- Notes and guidance:
-- * Unit: items (row per item in an event). item_revenue_sum is ITEM revenue aggregated across purchase item rows.
-- * Do not mix item_revenue_sum (item-level) with transaction-level revenue in the same column. If transaction revenue is required, extract it separately from the purchase event-level params.
-- * If item.item_revenue is not present and price/quantity are missing, revenue for those items will be estimated using the fallback and should be treated cautiously.
