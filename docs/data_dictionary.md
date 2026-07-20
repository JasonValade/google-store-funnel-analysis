# Data dictionary (selected fields)

This data dictionary lists commonly-used fields in the GA4 export and notes on where they typically appear. Always run `sql/00_schema_inspection.sql` to confirm the exact schema for your dataset/date range.

Top-level fields
- event_name: STRING — the name of the event (e.g., view_item, add_to_cart, purchase)
- event_timestamp: INTEGER — timestamp of the event in microseconds since epoch
- event_date: STRING — date in YYYYMMDD format
- user_pseudo_id: STRING — obfuscated user identifier
- items: ARRAY<STRUCT> — array of item records (item_id, item_name, price, quantity, etc.)
- event_params: ARRAY<STRUCT> — event parameters as key/value pairs (keys may include 'ga_session_id', 'engagement_time_msec', 'value', etc.)
- traffic_source: RECORD — with fields source, medium, name (subject to export configuration)
- device: RECORD — with fields category, mobile_brand_name, operating_system, etc.
- geo: RECORD — with fields country, region, city

Common item fields (inside items array)
- item_id: STRING
- item_name: STRING
- price: FLOAT
- quantity: INTEGER
- item_revenue: FLOAT (may or may not exist in the obfuscated sample)

Common event_params keys (examples)
- ga_session_id (INT/STRING): session identifier
- engagement_time_msec (INT): engagement time in milliseconds
- value / purchase_revenue / transaction_revenue (FLOAT/INT): potential transaction value fields

Notes on nested structures
- Use UNNEST(items) to explode item-level records. Be careful: UNNEST will produce one row per item per event and is appropriate for item-level aggregation.
- Use UNNEST(event_params) to extract parameter keys and values. parameter values may be in int_value, double_value, string_value, or float_value depending on the key.

Sessionization
- If ga_session_id is present in event_params, it is the preferred session identifier. If absent, sessionization may be approximated using event_timestamp gaps (not provided by default in this project).

