# Feature Documentation: Business Definitions

This document provides business-friendly definitions for all features used in the purchase propensity model. For technical implementation details, see `sql/09_model_features.sql`.

---

## Feature Categories

1. [Temporal Features](#temporal-features)
2. [Pre-View Engagement](#pre-view-engagement)
3. [First Item Information](#first-item-information)
4. [User Characteristics](#user-characteristics)
5. [Session Characteristics](#session-characteristics)

---

## Temporal Features

### seconds_to_first_view_log1p

**Technical:** Log-transformed time (in seconds) from session start to first product view.

**Business Definition:** How long the visitor spent browsing the site before looking at any products.

**Interpretation:**
- **Low values (< 10 seconds):** Visitor went directly to products (intent-driven)
- **Medium values (10-60 seconds):** Moderate browsing before products
- **High values (> 60 seconds):** Extensive browsing before products (research mode)

**Business Use:** Visitors who go directly to products may be more purchase-ready. Long browsing before products may indicate research mode.

---

### hour_sin, hour_cos

**Technical:** Cyclical encoding of the hour of day (0-23) using sine and cosine transformations.

**Business Definition:** Time of day when the session occurred, encoded to preserve that 23:00 is close to 00:00.

**Interpretation:**
- **Morning (6-12):** Workday browsing
- **Afternoon (12-18):** Lunch break or work browsing
- **Evening (18-24):** Personal shopping time
- **Night (0-6):** Late-night browsing

**Business Use:** Purchase behavior varies by time of day. Evening shoppers may be more purchase-inclined.

---

### dow_sin, dow_cos

**Technical:** Cyclical encoding of day of week (0=Sunday, 6=Saturday) using sine and cosine.

**Business Definition:** Day of week when the session occurred.

**Interpretation:**
- **Weekdays (Mon-Fri):** Workday browsing
- **Weekends (Sat-Sun):** Personal shopping time

**Business Use:** Weekend shoppers may have more time and higher purchase intent.

---

## Pre-View Engagement

### page_views_before_first_view_log1p

**Technical:** Log-transformed count of page views before the first product view.

**Business Definition:** How many pages the visitor viewed before looking at any products.

**Interpretation:**
- **0-1:** Direct navigation to products
- **2-5:** Moderate browsing
- **6+:** Extensive browsing

**Business Use:** Visitors who browse many pages before products may be in research mode. Direct navigation to products may indicate intent.

---

### scroll_events_before_first_view_log1p

**Technical:** Log-transformed count of scroll events before the first product view.

**Business Definition:** How much the visitor scrolled through pages before looking at products.

**Interpretation:**
- **Low values:** Minimal scrolling (quick skimming)
- **High values:** Deep content engagement

**Business Use:** High scrolling may indicate thorough readers who are evaluating options carefully.

---

### search_events_before_first_view_log1p

**Technical:** Log-transformed count of search events before the first product view.

**Business Definition:** How many times the visitor used the site search before looking at products.

**Interpretation:**
- **0:** No search (browsing navigation)
- **1+:** Active search for specific items

**Business Use:** Visitors who search may have specific intent and be closer to purchase.

---

### promotion_views_before_first_view_log1p

**Technical:** Log-transformed count of promotion view events before the first product view.

**Business Definition:** How many promotional banners or offers the visitor viewed before products.

**Interpretation:**
- **0:** Did not engage with promotions
- **1+:** Engaged with promotional content

**Business Use:** Promotion viewers may be price-sensitive or deal-seeking.

---

### engagement_events_before_first_view_log1p

**Technical:** Log-transformed count of general engagement events before the first product view.

**Business Definition:** Overall engagement level before looking at products.

**Interpretation:**
- **Low values:** Minimal engagement
- **High values:** Highly engaged visitor

**Business Use:** Highly engaged visitors before product viewing may be more invested in the shopping experience.

---

## First Item Information

### first_item_name_[product_name]

**Technical:** One-hot encoded product name of the first item viewed.

**Business Definition:** The specific product the visitor viewed first in the session.

**Interpretation:**
- Different products have different conversion rates
- Some product categories (e.g., Android Wear) may indicate higher intent
- Expensive items may indicate serious consideration

**Business Use:** First product viewed is a strong signal of purchase intent. Some items convert much better than others.

---

### first_item_category_[category]

**Technical:** One-hot encoded category of the first item viewed.

**Business Definition:** The product category of the first item viewed (e.g., Apparel, Electronics, Accessories).

**Interpretation:**
- Categories have different conversion rates
- Some categories may be more impulse-driven
- Others may be more research-intensive

**Business Use:** Category-level patterns can inform merchandising and promotion strategies.

---

### first_item_price

**Technical:** Log-transformed price of the first item viewed.

**Business Definition:** Price point of the first product the visitor viewed.

**Interpretation:**
- **Low prices:** May indicate bargain hunters
- **High prices:** May indicate serious purchasers
- **Price range:** May indicate budget sensitivity

**Business Use:** Price point of first view can indicate visitor's budget and purchase readiness.

---

## User Characteristics

### is_new_visitor

**Technical:** Binary flag indicating if this is the user's first session.

**Business Definition:** Whether the visitor is new to the site or a returning customer.

**Interpretation:**
- **New visitors:** May need more trust-building
- **Returning visitors:** Already familiar with brand, may convert better

**Business Use:** Returning visitors typically have higher conversion rates. This is a strong baseline signal.

---

### country_[country_code]

**Technical:** One-hot encoded country of the visitor.

**Business Definition:** Geographic location of the visitor.

**Interpretation:**
- Different countries have different purchasing patterns
- Some regions may have higher average order values
- Shipping availability varies by country

**Business Use:** Geographic patterns can inform localization and shipping strategy.

---

### device_category_[device]

**Technical:** One-hot encoded device type (mobile, desktop, tablet).

**Business Definition:** What device the visitor is using.

**Interpretation:**
- **Mobile:** On-the-go browsing, may convert differently
- **Desktop:** May indicate more serious shopping
- **Tablet:** Middle ground between mobile and desktop

**Business Use:** Device type influences user experience and conversion patterns.

---

### acquisition_source_[source]

**Technical:** One-hot encoded first-touch acquisition source (e.g., google, direct, youtube).

**Business Definition:** How the user first came to the site (original acquisition channel).

**Interpretation:**
- **Direct:** Returning visitors or type-in traffic
- **Google:** Organic search
- **YouTube:** Video discovery
- **Other:** Various referral sources

**Business Use:** First-touch source indicates long-term user value patterns. Note: This is first-touch, not session-level attribution.

---

### acquisition_medium_[medium]

**Technical:** One-hot encoded first-touch acquisition medium (e.g., organic, cpc, referral).

**Business Definition:** The medium of the user's first acquisition.

**Interpretation:**
- **Organic:** Natural search traffic
- **CPC:** Paid search traffic
- **Referral:** Traffic from other sites
- **(none):** Direct traffic

**Business Use:** Medium provides additional context on acquisition quality.

---

## Session Characteristics

### long_pre_view_session

**Technical:** Binary flag for sessions with > 30 seconds before first product view.

**Business Definition:** Whether the visitor spent significant time browsing before looking at products.

**Interpretation:**
- **True:** Extended browsing before products (research mode)
- **False:** Quick navigation to products (intent mode)

**Business Use:** Long pre-view sessions may indicate research mode, while short sessions may indicate purchase intent.

---

### item_metadata_missing

**Technical:** Binary flag for sessions where item information was missing from events.

**Business Definition:** Whether the session had incomplete product data.

**Interpretation:**
- **True:** Tracking issues or data quality problems
- **False:** Complete product data available

**Business Use:** This flag identifies sessions with potential data quality issues. May correlate with tracking problems.

---

## Feature Engineering Notes

### Log Transformations

**Why:** Many features have skewed distributions (many low values, few high values).

**Method:** Applied `log1p(x) = log(x + 1)` to handle zeros while reducing skew.

**Benefit:** Makes features more normally distributed, which helps many machine learning algorithms.

---

### One-Hot Encoding

**Why:** Machine learning models require numerical input, but many features are categorical.

**Method:** Each category becomes a binary column (1 if present, 0 if not).

**Example:** `device_category` becomes `device_category_mobile`, `device_category_desktop`, `device_category_tablet`.

**Limitation:** High-cardinality features (many categories) can increase dimensionality significantly.

---

### Cyclical Encoding

**Why:** Time features (hour, day of week) are cyclical (23:00 is close to 00:00).

**Method:** Use both sine and cosine transformations to preserve cyclical relationship.

**Benefit:** Model understands that 23:00 and 00:00 are close, unlike simple integer encoding.

---

## Feature Importance

Based on the Random Forest model, the most predictive features are:

1. **Item category** - Most predictive signal
2. **Device type** - Mobile vs. desktop behavior
3. **Pre-view engagement** - How users browse before products
4. **Time features** - Hour and day of week
5. **User characteristics** - New vs. returning visitor

---

## Business Applications

### High-Intent Identification

**Features that indicate high purchase intent:**
- Low `seconds_to_first_view` (direct to products)
- High `search_events_before_first_view` (specific intent)
- Returning visitor (`is_new_visitor = False`)
- High-value first item viewed

**Action:** Target these visitors with promotions or priority support.

### Research Mode Detection

**Features that indicate research mode:**
- High `seconds_to_first_view`
- High `page_views_before_first_view`
- High `scroll_events_before_first_view`
- Long pre-view session

**Action:** Provide educational content, comparisons, and social proof to build confidence.

### Price Sensitivity Signals

**Features that may indicate price sensitivity:**
- Low first item price
- High promotion views
- Engagement with deals

**Action:** Offer discounts or bundle deals to convert.

---

## Limitations

1. **First-Touch Attribution:** Acquisition features describe first touch, not session-level attribution
2. **Single Item Focus:** Only captures first item viewed, not full browsing history
3. **Temporal Scope:** Features only capture behavior up to first product view
4. **GA4 Limitations:** Some data quality issues in early November
5. **Obfuscated Data:** Public dataset is anonymized, limiting some insights

---

## Future Enhancements

1. **Full Browsing History:** Capture all items viewed, not just first
2. **Session-Level Attribution:** Implement proper attribution tracking
3. **Real-Time Features:** Add live session behavior signals
4. **Geographic Detail:** Add city/region-level features
5. **Behavioral Segments:** Create pre-defined user segments
6. **Cross-Session Features:** Incorporate historical behavior patterns
