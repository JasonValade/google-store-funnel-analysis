"""
Analysis Journey — The Thought Process Behind the Analysis

This page walks through the analytical journey, showing how we moved from
raw data to actionable insights. It demonstrates the data science process
from exploration to modeling to business recommendations.
"""

import streamlit as st

from dashboard.utils.data_loader import inject_global_styles, render_page_header


def main() -> None:
    inject_global_styles()
    render_page_header(
        "Analysis Journey",
        "From raw events to actionable insights — the complete analytical process",
        icon="🧭",
    )

    # Initialize session state for accordion expansion
    if "expanded_section" not in st.session_state:
        st.session_state.expanded_section = None

    # Visual Timeline
    st.markdown(
        """
    <div style="background: linear-gradient(90deg, rgba(79,140,255,0.1) 0%, rgba(37,99,235,0.05) 100%);
                border: 1px solid rgba(79, 140, 255, 0.2);
                border-radius: 12px;
                padding: 1.5rem;
                margin-bottom: 2rem;">
        <div style="font-size: 0.85rem; opacity: 0.7; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700;">
            Analysis Timeline
        </div>
        <div style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
            <span style="background: rgba(79,140,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">🎯 Problem</span>
            <span style="opacity: 0.5;">→</span>
            <span style="background: rgba(79,140,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">🔍 Data</span>
            <span style="opacity: 0.5;">→</span>
            <span style="background: rgba(79,140,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">📊 Funnel</span>
            <span style="opacity: 0.5;">→</span>
            <span style="background: rgba(79,140,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">🎯 Segments</span>
            <span style="opacity: 0.5;">→</span>
            <span style="background: rgba(79,140,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">🔔 Monitor</span>
            <span style="opacity: 0.5;">→</span>
            <span style="background: rgba(79,140,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">⚙️ Features</span>
            <span style="opacity: 0.5;">→</span>
            <span style="background: rgba(79,140,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">🤖 Model</span>
            <span style="opacity: 0.5;">→</span>
            <span style="background: rgba(79,140,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">💡 Insights</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Section 1: Understanding the Problem
    st.markdown("## 🎯 Phase 1: Understanding the Problem")

    with st.expander("Business Question & Objectives", expanded=True):
        st.markdown(
            """
        ### The Core Question
        **Where do customers abandon the purchase journey, which segments and products underperform,
        and can early-session behavior identify visitors who are more likely to purchase?**

        ### Objectives
        1. **Funnel Analysis** - Identify conversion bottlenecks
        2. **Segmentation** - Understand performance by device, channel, and product
        3. **Monitoring** - Detect tracking issues that could distort analysis
        4. **Prediction** - Build a model to identify high-intent visitors

        ### Why This Matters
        - **86% of product-view sessions never begin checkout** - massive opportunity
        - Marketing spend optimization - target high-intent visitors
        - Product assortment decisions - identify underperforming items
        - Tracking quality assurance - ensure data reliability
        """
        )

    # Section 2: Data Exploration
    st.markdown("## 🔍 Phase 2: Data Exploration & Quality Assessment")

    with st.expander("Data Source & Schema"):
        st.markdown(
            """
        ### Source
        **Dataset:** `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
        - **Scope:** November 2020 - January 2021 (holiday period)
        - **Volume:** 4.3 million events across 360,129 sessions
        - **Cost:** Free tier (public dataset)

        ### Key Challenge: Nested Fields
        GA4 uses nested structures:
        - `event_params` - Array of event-specific parameters
        - `items` - Array of item information for e-commerce events

        **Solution:** Used `UNNEST()` to extract relevant fields:
        ```sql
        UNNEST(event_params) AS params
        WHERE params.key = 'page_location'
        ```

        ### Important Fields
        - `event_name` - Event type (page_view, view_item, add_to_cart, etc.)
        - `event_timestamp` - Microsecond precision
        - `user_pseudo_id` - Anonymous user ID
        - `ga_session_id` - Session identifier
        """
        )

    with st.expander("Data Quality Issues Discovered"):
        st.markdown(
            """
        ### 🚨 Critical Finding: Tracking Outages

        During initial exploration, discovered major tracking issues:

        | Date Range | Issue | Impact |
        |------------|-------|--------|
        | Nov 1-15 | Unreliable `add_to_cart` counts | Near-zero events despite traffic |
        | Nov 21-24 | Complete `add_to_cart` outage | Zero events for 4 days |
        | Variable | Item ID inconsistency | Same product had different IDs |

        ### Decisions Made
        1. **Restricted funnel analysis** to dates with reliable tracking (Nov 16-20, Nov 25-Jan 31)
        2. **Normalized product names** instead of using inconsistent item IDs
        3. **Documented limitations** prominently in all outputs

        ### Why This Matters
        - Including unreliable data would distort funnel metrics
        - Normalization enabled product-level analysis
        - Transparency builds trust in results
        """
        )

        st.markdown(
            """
        <div style="background: rgba(255, 87, 87, 0.1); border: 1px solid rgba(255, 87, 87, 0.3); border-radius: 8px; padding: 1rem; margin-top: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem;">⚠️</span>
                <span style="font-weight: 700; color: rgba(255, 87, 87, 0.9);">Key Insight</span>
            </div>
            <div style="font-size: 0.9rem; opacity: 0.9;">
                Data quality is foundational. Garbage in = garbage out. Always validate data quality before analysis.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Section 3: Funnel Construction
    st.markdown("## 📊 Phase 3: Funnel Definition & Construction")

    with st.expander("Initial Approach vs. Refined Approach"):
        st.markdown(
            """
        ### ❌ Initial Approach: Simple Event Counting
        Count each event type and calculate conversion rates.

        **Problems:**
        - Doesn't account for multiple events per session
        - Doesn't require temporal ordering (purchase before view?)
        - Doesn't handle skipped stages (purchase without cart)

        ### ✅ Refined Approach: Session-Level Ordered Funnel

        **Key Decisions:**

        1. **Session Key:** `user_pseudo_id || '_' || ga_session_id`
           - Combines user ID with session ID for unique session identification

        2. **Strict Timestamp Ordering:**
           ```
           view_item → add_to_cart → begin_checkout → purchase
           ```
           Each stage must occur in chronological order.

        3. **Reliable Tracking Window:**
           - Only dates with confirmed `add_to_cart` reliability
           - Excludes Nov 1-15 and Nov 21-24

        ### Result
        | Stage | Sessions | Conversion |
        |-------|----------|------------|
        | Product view | 77,020 | — |
        | Begin checkout | 10,770 | 13.98% |
        | Purchase | 4,661 | 43.28% from checkout |
        | **Overall** | — | **6.05%** |

        **Key Insight:** 86% of product-view sessions never begin checkout.
        """
        )

        st.markdown(
            """
        <div style="background: rgba(79, 140, 255, 0.1); border: 1px solid rgba(79, 140, 255, 0.3); border-radius: 8px; padding: 1rem; margin-top: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem;">🎯</span>
                <span style="font-weight: 700; color: rgba(79, 140, 255, 0.9);">Biggest Opportunity</span>
            </div>
            <div style="font-size: 0.9rem; opacity: 0.9;">
                86% checkout abandonment represents the largest optimization opportunity. If we capture just 10% more checkouts: ~1,000 additional purchases/month = $50K-$100K additional revenue.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with st.expander("Alternative Funnel for ML Modeling"):
        st.markdown(
            """
        ### Broader Definition for Machine Learning

        For the propensity model, we used a **broader funnel definition**:

        **Requirement:** Purchase must occur after first `view_item`
        - No requirement for `add_to_cart` or `begin_checkout`
        - Captures sessions that purchase via non-standard paths

        **Result:** 4,688 sessions (vs. 4,661 in ordered funnel)
        - 27 additional sessions purchased without completing all stages
        - More training data for the model
        - Better represents real-world purchase behavior

        **Model prevalence:** 6.09% (vs. 6.05% in ordered funnel)
        """
        )

    # Section 4: Segmentation Analysis
    st.markdown("## 🎯 Phase 4: Segmentation Analysis")

    with st.expander("Device Segmentation"):
        st.markdown(
            """
        ### Finding: Mobile Slightly Outperforms Desktop

        | Device | Conversion Rate | Statistically Significant? |
        |--------|----------------|---------------------------|
        | Mobile | 6.26% | Borderline (p ≈ 0.06) |
        | Desktop | 5.91% | — |
        | Tablet | 5.50% | — |

        ### Interpretation
        - Mobile optimization is strong
- Difference exists but may not be practically significant
- Focus on desktop experience parity

        ### Why Statistical Context Matters
        Without statistical testing, we might overinvest in mobile improvements
        when the difference could be random variation.
        """
        )

    with st.expander("Traffic Source Analysis"):
        st.markdown(
            """
        ### Finding: Direct Traffic Converts Best

        | Channel | Conversion Rate |
        |---------|----------------|
        | Direct | 5.92% |
        | Google Organic | 5.08% |
        | Google CPC | 4.74% |

        ### ⚠️ Critical Limitation
        GA4 provides `first_user_source` and `first_user_medium`:
- These describe the **user's first acquisition**, not the current session
- A returning user always shows their original acquisition channel

        ### Recommendation
        - Audit self-referral rates (may inflate direct traffic)
        - Validate attribution accuracy before reallocating ad spend
        - Consider session-level attribution for future analysis
        """
        )

    with st.expander("Product-Level Analysis"):
        st.markdown(
            """
        ### Finding: High-Traffic, Low-Conversion Products

        Several products had 1-2% conversion rates vs. 6% average.

        ### 🔍 Investigation Required Before Action

        These could indicate:
        - **Merchandising issues** - Products customers don't want
        - **Inventory issues** - Out of stock but still browsable
        - **Tracking issues** - Events not firing correctly
        - **UX issues** - Confusing product pages

        ### Approach
        1. Audit inventory availability
        2. Verify tracking instrumentation
        3. Check product page UX
        4. Then consider merchandising changes

        ### Why This Matters
        Taking action based on incomplete investigation could:
        - Remove products that are actually popular but have tracking issues
        - Miss inventory problems that are easily fixable
        - Waste time on UX changes when the real issue is inventory
        """
        )

    # Section 5: Tracking Health Monitoring
    st.markdown("## 🔔 Phase 5: Tracking Health Monitoring")

    with st.expander("The Problem: Detecting Tracking Failures"):
        st.markdown(
            """
        ### Challenge
        During exploration, discovered `add_to_cart` events dropped to zero
        on specific dates despite continued page views.

        **Question:** Is this a tracking failure or legitimate behavior change?

        ### Signal Design

        We built a monitoring system with multiple signals:

        1. **Rolling 7-day baseline** - Expected event count based on recent history
        2. **Event-volume ratio** - Actual count / baseline
        3. **Z-score** - Statistical deviation from expected
        4. **Page-view context** - Event count / page view count
        5. **Traffic-adjusted ratio** - Normalized by session volume

        ### Thresholds
        - Event-volume ratio < 0.5 → Potential tracking failure
        - Page-view ratio < 0.5 → Event-specific issue (not general traffic decline)
        - Z-score > 3 → Statistically significant deviation
        """
        )

    with st.expander("Validation & Results"):
        st.markdown(
            """
        ### Manual Validation
        Manually confirmed four outage dates (Nov 21-24) by checking event counts.

        ### Monitor Performance
        ✅ Correctly identified all four confirmed outages
        ✅ Distinguished tracking failures from traffic declines
        ✅ False positive rate acceptable for prototype

        ### Classification
        | Date | Event Volume Ratio | Page View Ratio | Classification |
        |------|-------------------|-----------------|----------------|
        | Nov 21 | 0.00 | 0.68 | CRITICAL OUTAGE |
        | Nov 22 | 0.00 | 0.72 | CRITICAL OUTAGE |
        | Nov 23 | 0.00 | 0.65 | CRITICAL OUTAGE |
        | Nov 24 | 0.00 | 0.70 | CRITICAL OUTAGE |
        | Nov 25 | 0.45 | 0.95 | LIKELY TRAFFIC DECLINE |

        ### Business Value
        Automated monitoring enables:
        - Quick detection of tracking failures
        - Prevention of business decisions based on bad data
        - Improved data quality culture
        """
        )

    # Section 6: Feature Engineering
    st.markdown("## ⚙️ Phase 6: Feature Engineering for Prediction")

    with st.expander("Problem Statement & Constraints"):
        st.markdown(
            """
        ### Question
        Can early-session behavior predict whether a purchase will occur later?

        ### Critical Constraint: No Leakage
        **Use only information available at the time of the first `view_item` event.**

        Why? Using future information (e.g., total time on site, number of page views)
        would create leakage - the model would "cheat" by seeing information that
        wouldn't be available at prediction time.

        ### Implementation
        Feature extraction in SQL ensures temporal separation:
        ```sql
        WHERE event_timestamp <= first_view_timestamp
        ```
        """
        )

    with st.expander("Feature Categories"):
        st.markdown(
            """
        ### 1. Temporal Features
        - `seconds_to_first_view` - Time from session start to first product view
        - `hour_sin`, `hour_cos` - Cyclical encoding of hour of day
        - `dow_sin`, `dow_cos` - Cyclical encoding of day of week

        **Rationale:** Purchase behavior varies by time (evening shopping, weekend purchases).
        Cyclical encoding preserves temporal proximity (23:00 is close to 00:00).

        ### 2. Pre-View Engagement
        - `page_views_before_first_view`
        - `scroll_events_before_first_view`
        - `search_events_before_first_view`
        - `promotion_views_before_first_view`

        **Rationale:** Users who browse/search before viewing products may be in
        different purchase mindsets (research vs. intent).

        **Transformation:** Applied `log1p` to handle skewed distributions.

        ### 3. First Item Information
        - `first_item_name` - One-hot encoded product name
        - `first_item_category` - One-hot encoded category
        - `first_item_price` - Log-transformed price

        **Rationale:** First product viewed may indicate user intent (expensive vs. clearance).

        ### 4. User Characteristics
        - `is_new_visitor` - First-time user flag
        - `country` - One-hot encoded country
        - `device_category` - One-hot encoded device type
        - `acquisition_source` - First-touch acquisition source

        **Rationale:** User context influences purchase likelihood.

        ### 5. Session Characteristics
        - `long_pre_view_session` - Flag for > 30 seconds before first view
        - `item_metadata_missing` - Flag for missing item information

        **Rationale:** Long browsing before viewing may indicate research vs. purchase intent.
        """
        )

    with st.expander("Feature Validation"):
        st.markdown(
            """
        ### Validation Checks Performed

        1. **Timestamp ordering** - Ensure feature times ≤ purchase times
        2. **Missing value analysis** - Identify features with high missingness
        3. **Distribution checks** - Identify extreme outliers
        4. **Correlation analysis** - Detect highly correlated features

        ### Decisions
        - Dropped features with > 50% missing values
        - Applied log transformation to skewed numerical features
        - One-hot encoded categorical features with < 20 levels
        - Grouped rare categories into "Other"

        ### Feature Count
        - **Final features:** ~100 after encoding
        - **Sessions:** 77,020
        - **Features per session:** 100+
        """
        )

        st.markdown(
            """
        <div style="background: rgba(0, 153, 136, 0.1); border: 1px solid rgba(0, 153, 136, 0.3); border-radius: 8px; padding: 1rem; margin-top: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem;">🔒</span>
                <span style="font-weight: 700; color: rgba(0, 153, 136, 0.9);">Leakage Prevention</span>
            </div>
            <div style="font-size: 0.9rem; opacity: 0.9;">
                Strict temporal separation: Features only use data BEFORE first view_item. Target only considers purchases AFTER first view_item. This prevents the model from "cheating" with future information.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Section 7: Model Development
    st.markdown("## 🤖 Phase 7: Model Development & Evaluation")

    with st.expander("Problem Framing & Metrics"):
        st.markdown(
            """
        ### Task
        Binary classification: predict whether a purchase occurs in a session

        **Label:** `purchased_later_in_session` (1 if purchase after first view, 0 otherwise)

        **Imbalance:** 6.09% of sessions result in purchase (imbalanced classification)

        ### Metric Selection: PR-AUC

        **Why PR-AUC over ROC-AUC?**
        - Appropriate for imbalanced classification
        - Focuses on positive class (purchases)
        - More informative when class imbalance is high
        - Precision-Recall tradeoff is more relevant for business decisions

        **Alternative metrics reported:**
        - ROC-AUC: 0.7876
        - Brier score: 0.0457 (calibration)
        - Lift at top decile: 3.12×
        """
        )

    with st.expander("Train/Validation/Test Split"):
        st.markdown(
            """
        ### Chronological Split to Prevent Leakage

        | Set | Date Range | Sessions | Purchase Rate |
        |-----|------------|----------|---------------|
        | Train | Nov 16 - Dec 15 | ~50K | 6.09% |
        | Validation | Dec 16 - Dec 31 | ~12K | 5.8% |
        | Test | Jan 1 - Jan 31 | ~15K | 5.04% |

        **Rationale:** Time-based split simulates real-world deployment where
        the model predicts future behavior.

        **Drift Notice:** Test set prevalence (5.04%) lower than train (6.09%)
        due to post-holiday decline. This is realistic and expected.
        """
        )

    with st.expander("Model Comparison"):
        st.markdown(
            """
        ### Models Evaluated

        | Model | PR-AUC | ROC-AUC | Interpretability |
        |-------|--------|---------|------------------|
        | Dummy (baseline) | 0.0504 | 0.500 | N/A |
        | Logistic Regression | 0.1285 | 0.752 | High (coefficients) |
        | Random Forest | 0.1402 | 0.788 | Medium (feature importance) |

        **Decision:** Selected Random Forest for final model
        - Best performance (PR-AUC = 0.1402 vs. 0.0504 baseline)
        - Still interpretable via feature importance
        - Handles non-linear relationships

        **Key Finding:** Model provides **2.78× improvement** over no-skill baseline.
        """
        )

        st.markdown(
            """
        <div style="background: rgba(0, 153, 136, 0.1); border: 1px solid rgba(0, 153, 136, 0.3); border-radius: 8px; padding: 1rem; margin-top: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem;">📈</span>
                <span style="font-weight: 700; color: rgba(0, 153, 136, 0.9);">Model Performance</span>
            </div>
            <div style="font-size: 0.9rem; opacity: 0.9;">
                Random Forest PR-AUC: 0.1402 vs. Baseline: 0.0504 = 2.78× improvement. The model successfully identifies high-intent visitors with 3.12× lift in the top decile.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with st.expander("Feature Importance & Interpretation"):
        st.markdown(
            """
        ### Top Predictive Features

        **From Logistic Regression (coefficients):**
- Positive associations → higher purchase probability
- Negative associations → lower purchase probability
- ⚠️ **Caveat:** Associations are not causal effects

        **From Random Forest (feature importance):**
- Item category is most predictive
- Device type matters
- Pre-view engagement metrics are important

        **Interpretation:**
- Product category is the strongest signal (some items sell better)
- Mobile users have slightly higher propensity
- Users who engage before viewing products are more likely to purchase
        """
        )

    with st.expander("Calibration & Decile Analysis"):
        st.markdown(
            """
        ### Calibration: Are Probabilities Well-Calibrated?

        **Approach:** Sigmoid calibration (Platt scaling) on validation set

        **Result:** Calibration improved but not perfect
- Model slightly overestimates low-probability cases
- High-probability predictions are fairly accurate

        **Brier score:** 0.0457 (lower is better)
- Perfect classifier: 0
- Random guessing: 0.06
- Our model: 0.0457

        ### Decile Analysis: Business Impact

        **Approach:** Rank sessions by predicted probability, divide into 10 deciles

        **Result:**
        | Decile | Purchase Rate | Lift | % of Purchases |
        |--------|---------------|------|-----------------|
        | 1 (highest) | 15.73% | 3.12× | 31.3% |
        | 2-10 | 3.6% | 0.71× | 68.7% |
        | Overall | 5.04% | 1.0× | 100% |

        **Business Application:**
- Top 10% of sessions capture 31.3% of purchases
- Target high-decile sessions for interventions (promotions, support)
- 3.12× lift means 3x more likely to purchase than average
        """
        )

    # Section 8: Recommendations
    st.markdown("## 💡 Phase 8: Recommendations & Next Steps")

    with st.expander("Business Recommendations"):
        st.markdown(
            """
        ### Immediate Actions (0-30 days)

        1. **Reduce checkout friction**
           - Test guest checkout option
           - Display shipping costs early
           - Simplify checkout form fields

        2. **Audit low-converting products**
           - Review inventory availability
           - Verify tracking instrumentation
           - Check product page UX

        3. **Implement tracking health alerts**
           - Set up automated monitoring
           - Create alert notification system

        ### Medium-Term (1-3 months)

        4. **A/B test checkout optimizations**
           - Single-page vs. multi-page checkout
           - Shipping cost transparency
           - Account requirement impact

        5. **Propensity scoring pilot**
           - Deploy model to identify high-intent visitors
           - Test targeted interventions
           - Monitor conversion lift

        6. **Attribution investigation**
           - Audit self-referral rates
           - Validate channel attribution
           - Re-evaluate budget allocation

        ### Long-Term (3-6 months)

        7. **Personalization framework**
           - Build on propensity model
           - Segment-specific messaging

        8. **Real-time analytics**
           - Live dashboard deployment
           - Integration with production systems
        """
        )

    with st.expander("Limitations & Caveats"):
        st.markdown(
            """
        ### Data Limitations
        - Public dataset is obfuscated (no real user data)
        - Covers only Nov 2020 - Jan 2021 (holiday period)
        - Some tracking reliability issues during analysis period
        - Acquisition fields describe first touch, not session-level

        ### Analysis Limitations
        - Item ID inconsistency required normalization
        - Funnel analysis restricted to reliable tracking dates
        - Model associations are correlational, not causal
        - Recommendations require A/B testing validation

        ### Deployment Limitations
        - Dashboard uses pre-computed artifacts (not live data)
        - Model requires monitoring for calibration drift
        - Tracking monitoring is a prototype (needs productionization)
        """
        )

    # Section 9: Key Learnings
    st.markdown("## 📚 Key Learnings & Retrospective")

    # Visual Summary Card
    st.markdown(
        """
    <div style="background: linear-gradient(135deg, rgba(79,140,255,0.15) 0%, rgba(37,99,235,0.1) 100%);
                border: 1px solid rgba(79, 140, 255, 0.3);
                border-radius: 16px;
                padding: 2rem;
                margin-bottom: 2rem;">
        <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 1.5rem; color: rgba(79, 140, 255, 0.95);">
            🎯 Three Key Takeaways
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
            <div style="background: rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 1rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">86%</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">of product viewers never start checkout</div>
                <div style="font-size: 0.75rem; opacity: 0.6; margin-top: 0.5rem;">Biggest opportunity</div>
            </div>
            <div style="background: rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 1rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">3.12×</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">lift in top decile</div>
                <div style="font-size: 0.75rem; opacity: 0.6; margin-top: 0.5rem;">Model performance</div>
            </div>
            <div style="background: rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 1rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">$180K</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">-$360K annual revenue opportunity</div>
                <div style="font-size: 0.75rem; opacity: 0.6; margin-top: 0.5rem;">Business impact</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.expander("What Worked Well"):
        st.markdown(
            """
        ✅ **Strict temporal separation** in feature engineering prevented leakage
        ✅ **Manual tracking validation** confirmed monitoring signals were accurate
        ✅ **Multi-page dashboard** allowed both business and technical audiences
        ✅ **Pre-computed artifacts** made deployment simple and secure
        ✅ **Statistical context** prevented overinterpretation of small differences
        ✅ **Documentation** of limitations built trust in results
        """
        )

    with st.expander("Challenges Faced"):
        st.markdown(
            """
        ⚠️ **GA4 data complexity** - Nested fields required significant SQL engineering
        ⚠️ **Tracking reliability** - Had to exclude early November from funnel analysis
        ⚠️ **Item ID inconsistency** - Required product name normalization
        ⚠️ **Class imbalance** - Required careful metric selection (PR-AUC vs ROC-AUC)
        ⚠️ **Acquisition attribution** - First-touch fields limited channel analysis
        ⚠️ **Temporal drift** - Post-holiday decline affected test set prevalence
        """
        )

    with st.expander("What I'd Do Differently"):
        st.markdown(
            """
        🔄 **Earlier A/B test planning** - Would design experiments alongside analysis
        🔄 **Real-time monitoring** - Would implement automated alerts sooner
        🔄 **Feature documentation** - Would create data dictionary earlier
        🔄 **Model monitoring plan** - Would define drift detection criteria upfront
        🔄 **Stakeholder alignment** - Would align on metrics before building dashboard
        🔄 **Session-level attribution** - Would implement better tracking for future analysis
        """
        )

    # Footer
    st.markdown("---")
    st.markdown(
        """
    ### 📖 Full Documentation

    For more detailed technical documentation, see:
    - [Executive Summary](../docs/executive_summary.md) - Business-focused overview
    - [Executive Presentation](../docs/executive_presentation.md) - Slide deck for stakeholders
    - [Visual Story](../docs/visual_story.md) - Narrative walkthrough with visuals
    - [A/B Testing Framework](../docs/ab_testing_framework.md) - Experimentation guide
    - [Technical Methodology](../docs/technical_methodology.md) - Deep technical dive
    - [Feature Documentation](../docs/feature_documentation.md) - Business feature definitions
    - [Model Methodology](../reports/model_methodology.md) - ML-specific details
    - [Metric Definitions](../docs/metric_definitions.md) - Business metric definitions
    - [Data Dictionary](../docs/data_dictionary.md) - Field descriptions
    """
    )

    st.markdown(
        """
    <div style="text-align: center; opacity: 0.7; margin-top: 2rem;">
        This analysis demonstrates the complete data science workflow: from raw event data
        to actionable business insights, with technical rigor in feature engineering,
        model development, and evaluation.
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Process Flow Visualization
    st.markdown(
        """
    <div style="background: rgba(79, 140, 255, 0.05); border: 1px solid rgba(79, 140, 255, 0.2); border-radius: 12px; padding: 1.5rem; margin-top: 2rem;">
        <div style="text-align: center; font-size: 0.85rem; opacity: 0.7; margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700;">
            The Data Science Workflow
        </div>
        <div style="display: flex; justify-content: center; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
            <div style="background: rgba(79, 140, 255, 0.15); padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.85rem; font-weight: 600;">Raw Data</div>
            <span style="opacity: 0.4;">→</span>
            <div style="background: rgba(79, 140, 255, 0.15); padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.85rem; font-weight: 600;">Quality Check</div>
            <span style="opacity: 0.4;">→</span>
            <div style="background: rgba(79, 140, 255, 0.15); padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.85rem; font-weight: 600;">Analysis</div>
            <span style="opacity: 0.4;">→</span>
            <div style="background: rgba(79, 140, 255, 0.15); padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.85rem; font-weight: 600;">Modeling</div>
            <span style="opacity: 0.4;">→</span>
            <div style="background: rgba(79, 140, 255, 0.15); padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.85rem; font-weight: 600;">Insights</div>
            <span style="opacity: 0.4;">→</span>
            <div style="background: rgba(0, 153, 136, 0.2); padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.85rem; font-weight: 600; color: rgba(0, 153, 136, 0.9);">Action</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
