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

---

## V3 model feature table

The fields below are produced by `sql/09_model_features.sql` and stored in `data/processed/demo/model_features.csv.gz`. Each row represents one GA4 session that contains at least one `view_item` event. The prediction moment is immediately after the session's first `view_item` event; no field may use information from after that timestamp.

### Identifiers and split fields

| Field | Type | Role | Definition | Available at prediction time |
|---|---|---|---|---|
| `session_id` | STRING | Identifier | `CONCAT(user_pseudo_id, '_', CAST(ga_session_id AS STRING))` — unique key for each session. NULL sessions are excluded. | N/A — not a model feature |
| `session_date` | DATE | Split field | Calendar date of the session, used to assign chronological train / validation / test splits. | N/A — not a model feature |
| `first_view_item_timestamp` | INTEGER | Prediction timestamp | Microsecond epoch timestamp of the session's first `view_item` event. Defines the prediction moment. | N/A — not a model feature |

### Model features

All features use only information available at or before `first_view_item_timestamp`.

| Field | Type | Role | Source GA4 field | Definition | Leakage risk |
|---|---|---|---|---|---|
| `device_category` | STRING | Feature | `device.category` | Device type reported by GA4 (e.g., `desktop`, `mobile`, `tablet`). `COALESCE(..., '(unknown)')` applied for missing values. | None |
| `country` | STRING | Feature | `geo.country` | Visitor's country from GA4 geo record. `COALESCE(..., '(unknown)')` applied for missing values. | None |
| `acquisition_source` | STRING | Feature | `traffic_source.source` | **First-user acquisition source** — reflects how the user was originally acquired, not session-level attribution. Not safe to interpret as the source driving this specific session. `COALESCE(..., '(unknown)')` applied. | None (but see caveat on acquisition scope) |
| `acquisition_medium` | STRING | Feature | `traffic_source.medium` | **First-user acquisition medium** — same caveat as `acquisition_source`. | None (but see caveat on acquisition scope) |
| `first_item_name` | STRING | Feature | `items[0].item_name` on the first `view_item` event | `LOWER(TRIM(...))` normalised name of the first item in the items array of the first `view_item` event. If the items array is empty or item_name is NULL, value is `'(unknown)'`. **Uses only the first item** in the array consistently across all sessions. | None — item is known at the view_item moment |
| `first_item_category` | STRING | Feature | `items[0].item_category` on the first `view_item` event | Product category of the first item in the first `view_item` event. `COALESCE(..., '(unknown)')` applied. | None — item is known at the view_item moment |
| `first_item_price` | FLOAT | Feature | `items[0].price` on the first `view_item` event | Listed price of the first item in the first `view_item` event. NULL when price is absent (~20,697 sessions). | None — item is known at the view_item moment |
| `hour_of_day` | INTEGER | Feature | `event_timestamp` of first `view_item` | Hour (0–23) of the first `view_item` event in UTC. | None |
| `day_of_week` | INTEGER | Feature | `event_timestamp` of first `view_item` | Day of the week of the first `view_item` event (1 = Sunday … 7 = Saturday, per BigQuery `EXTRACT(DAYOFWEEK …)`). | None |
| `seconds_from_session_start_to_first_view` | FLOAT | Feature | `event_timestamp` of `session_start` and first `view_item` | Elapsed seconds between the session's `session_start` event and the first `view_item`. Computed as `(first_view_item_timestamp − session_start_timestamp) / 1,000,000`. Should be ≥ 0. | None |
| `page_views_before_first_view` | INTEGER | Feature | `event_name = 'page_view'` | Count of `page_view` events with `event_timestamp < first_view_item_timestamp`. | None |
| `scroll_events_before_first_view` | INTEGER | Feature | `event_name = 'scroll'` | Count of `scroll` events strictly before the first `view_item`. | None |
| `search_events_before_first_view` | INTEGER | Feature | `event_name = 'search'` | Count of `search` events strictly before the first `view_item`. | None |
| `promotion_views_before_first_view` | INTEGER | Feature | `event_name = 'view_promotion'` | Count of `view_promotion` events strictly before the first `view_item`. | None |
| `engagement_events_before_first_view` | INTEGER | Feature | `event_name = 'user_engagement'` | Count of `user_engagement` events strictly before the first `view_item`. | None |
| `is_new_visitor` | INTEGER | Feature | `event_name = 'first_visit'` | 1 if a `first_visit` event occurred at or before the first `view_item` timestamp in this session; 0 otherwise. Does not use post-view data. | None |

### Target

| Field | Type | Role | Definition | Prediction-time availability |
|---|---|---|---|---|
| `purchased_later_in_session` | INTEGER | Target | 1 if a `purchase` event occurs **strictly after** `first_view_item_timestamp` in the same session; 0 otherwise. No fixed label window is imposed — the entire remainder of the session is used. | Not available at prediction time — this is what the model predicts |

### Missing-value notes

- `first_item_price` is NULL for approximately 20,697 sessions (26.9% of total). The modeling notebook uses median imputation inside the training pipeline and adds an `item_metadata_missing` indicator feature.
- `first_item_name` and `first_item_category` are `'(unknown)'` when the first `view_item` event's items array is empty or the field is NULL.
- `acquisition_source` and `acquisition_medium` fall back to `'(unknown)'` when `traffic_source` fields are missing.

### Obsolete fields (V2 draft model — no longer used)

The following fields appeared in an earlier draft of the model specification and have been removed. They are documented here for reference only.

| Field | Reason removed |
|---|---|
| `adds_in_obs_window` | Post-prediction behavior — `add_to_cart` events after `first_view_item_timestamp` are excluded to prevent leakage |
| `begins_in_obs_window` | Post-prediction behavior — `begin_checkout` events after the prediction moment are excluded |
| `purchase_during_observation` | Target-derived — recording the target value as a feature is direct leakage |
| Fixed ten-minute observation window | Replaced by the strict `event_timestamp < first_view_item_timestamp` rule; no arbitrary window is imposed |

