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

-- 06_product_analysis.sql (ARCHIVED)
-- This file has been superseded by sql/08_product_analysis.sql which prefers item.item_revenue when available and documents item vs transaction revenue distinctly.
-- Use sql/08_product_analysis.sql (unit: items) as the canonical product analysis.
-- This archived file is preserved for reference and should not be used for production reporting.

-- Notes:
-- * The obfuscated sample may not populate all item fields; inspect items in 02_data_quality
-- * extracted_value attempts several keys. Adjust as needed to align with your dataset's purchase revenue field
-- * Identify products with high views but low view_to_purchase_rate as opportunity candidates
