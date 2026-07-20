# Metric Definitions

This document defines key terms and metrics used throughout the project. Use these definitions when writing methodology, reproducing results, or building dashboards.

Event
- Definition: A single record in the GA4 export representing an interaction (e.g., page_view, view_item, add_to_cart, purchase).
- Notes: Events have an event_name and may carry nested fields (event_params) and arrays (items).

User
- Definition: Identified by user_pseudo_id in the GA4 export. Acts as an opaque identifier for a visitor across events in this dataset.
- Notes: user_pseudo_id is not personally identifiable information in this obfuscated sample but treat any identifier as sensitive in production.

Session
- Definition: A collection of events grouped into a browsing session. In GA4 export, a session identifier may be available in event_params under the key 'ga_session_id'.
- Implementation used here: session_id = CONCAT(user_pseudo_id, '_', ga_session_id) when ga_session_id exists. Sessions without ga_session_id are labeled '(unknown)'.
- Notes: If ga_session_id is not present, sessionization can be approximated using event_timestamp gaps (e.g., 30-minute inactivity threshold), but that approach is not used by default here.

Transaction / Purchase
- Definition: A purchase is represented by an event where event_name = 'purchase'. A single transaction may contain multiple items.
- Notes: Transaction-level revenue may be recorded in event_params or ecommerce fields on the purchase event; item-level revenue can be computed as SUM(item.price * item.quantity) when these fields are populated.

Funnel entry
- Definition: The funnel entry for this project is `view_item` (a user viewed a product). Depending on the analysis, you may also analyze broader funnels beginning with sessions or page_view events.

Conversion rate
- Definition: The proportion of units that move from one funnel stage A to a subsequent stage B.
- Formula: Conversion rate (A → B) = SAFE_DIVIDE(count_reached_B, count_reached_A)
- Units: conversion rates can be calculated on users, sessions, events, or transactions. Always state the unit used (e.g., user-level conversion).

Drop-off rate
- Definition: Proportion of units that do not progress from stage A to stage B.
- Formula: Drop-off = 1 - Conversion rate (A → B)

Purchase
- Definition: See Transaction / Purchase. For modeling targets, a purchase label is set when a purchase event occurs within the label window.

Revenue
- Definitions:
  - Item revenue: SUM(item.price * item.quantity) for purchase events where item.price and item.quantity are available. Represents revenue attributable to items only.
  - Transaction revenue: Revenue reported at the transaction/purchase event level (may include tax, shipping, discounts). Extract from event-level params (e.g., purchase_revenue, value) if present.
- Guidance: Run `sql/00_schema_inspection.sql` to confirm which revenue fields are present and which to use. Do not estimate transaction revenue from unrelated event parameters.

Traffic source
- Definition: The top-level fields traffic_source.source and traffic_source.medium in this GA4 export are typically populated to reflect first-user acquisition (the source/medium that brought the user). Treat these fields as first-user acquisition fields by default for analyses that compare cohorts by acquisition source.
- Attribution scope: Do NOT assume these fields represent session-level attribution. Before interpreting them as session attribution, check for session-level campaign parameters or a collected_traffic_source field in event_params or other session attributes using `sql/00_schema_inspection.sql`.
- Guidance: Inspect event_param keys and traffic_source fields using `sql/00_schema_inspection.sql`. If session-level campaign parameters are present and populated per session, document that you will use session-level attribution; otherwise, default to first-user acquisition semantics and state that choice in any report.

## Product Analysis

### Product-level aggregation methodology

- **Unit of analysis**: Sessions. Product-view sessions and purchase sessions are counted as distinct sessions using CONCAT(user_pseudo_id, '_', ga_session_id) as the session identifier.
- **Product key**: Normalized product names (LOWER(TRIM(item.item_name))) are used to match product views with purchases because:
  - Item IDs alone were unreliable (810 distinct item IDs in purchase events vs. 427 in view_item events)
  - Normalized names covered 93.55% of product-view sessions and 96.19% of purchase sessions
  - 388 normalized names appeared in both event types; 34 appeared only in views; 8 appeared only in purchases
- **Revenue calculation**: Prefer item.item_revenue when available. Fallback: item.price * item.quantity. Do not mix item-level and transaction-level revenue.
- **Minimum threshold**: Products must have ≥1,000 product-view sessions to reduce noise from low-traffic items.

### Opportunity status field

- **"Investigate availability or tracking"**: Products with zero purchases. Possible causes include unavailable items, discontinued SKUs, catalog changes, data obfuscation, or tracking problems. Not automatically proof of poor product design.
- **"High-traffic, low-conversion candidate"**: Products with purchase rate < 1% and ≥1,000 views. Candidates for further investigation (A/B testing, UX review, qualitative research).
- **"Monitor"**: Products with purchase rate ≥1%. Performing at acceptable baseline for the store.

---

