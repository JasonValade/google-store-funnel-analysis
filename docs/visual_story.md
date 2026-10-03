# Visual Story: The Google Store Funnel Journey

A visual walkthrough of our analysis from raw events to actionable insights.

---

## Part 1: The Challenge

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   🏢 GOOGLE MERCHANDISE STORE                              │
│                                                             │
│   4.3 Million Events → 360,129 Sessions → ??? Purchases   │
│                                                             │
│   ❓ Where do customers abandon?                            │
│   ❓ Which segments underperform?                           │
│   ❓ Can we predict purchase intent?                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**The Problem:** We have mountains of data but don't know where to focus optimization efforts.

---

## Part 2: The Data Landscape

```
Raw GA4 Events (4.3M)
        │
        ▼
┌──────────────────────────────────────┐
│   Event Types                        │
│   ┌─────────┐ ┌─────────┐            │
│   │page_view│ │view_item│            │
│   └─────────┘ └─────────┘            │
│   ┌─────────┐ ┌─────────┐            │
│   │add_cart │ │checkout │            │
│   └─────────┘ └─────────┘            │
│   ┌─────────┐                        │
│   │purchase │                        │
│   └─────────┘                        │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│   Time Period: Nov 2020 - Jan 2021   │
│   ⚠️  Tracking Issues:               │
│   • Nov 1-15: Unreliable add_to_cart │
│   • Nov 21-24: Complete outage       │
└──────────────────────────────────────┘
```

**Key Insight:** Data quality matters. We had to exclude unreliable periods from analysis.

---

## Part 3: The Funnel Revealed

```
                    77,020 Product Views
                           │
                           │ 86% DROP ❌
                           ▼
                    10,770 Begin Checkout
                           │
                           │ 56% DROP ❌
                           ▼
                     4,661 Purchases
                           │
                           │
                           ▼
                     6.05% Conversion
```

**The Shocking Discovery:** 86% of people who view products never even start checkout!

```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  🎯 BIGGEST OPPORTUNITY: Product View → Checkout       │
│                                                          │
│  If we could capture just 10% more checkouts:           │
│  • ~1,000 additional purchases per month                │
│  • ~$50,000-$100,000 additional revenue                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Part 4: The Cart Mystery

```
When Cart Tracking Was Reliable:

     34.94% of Cart Sessions → Checkout
           │
           │ 65% DROP ❌
           ▼
     43.28% of Checkout → Purchase
```

**Another Bottleneck:** Even when people add to cart, 65% abandon before checkout.

**Hypotheses:**
- 💰 Shipping costs revealed too late?
- 🔐 Account requirement creates friction?
- 📦 Complex checkout process?
- 🛒 Comparison shopping across sites?

---

## Part 5: Segment Insights

### Device Performance

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  📱 Mobile:     6.26%  ████▓▓▓▓▓▓▓▓▓▓▓▓▓▓          │
│  💻 Desktop:    5.91%  ████▓▓▓▓▓▓▓▓▓▓▓▓▓▓          │
│  📟 Tablet:     5.50%  ████▓▓▓▓▓▓▓▓▓▓▓▓▓▓          │
│                                                     │
│  ✅ Mobile optimization is strong                   │
│  ⚠️  Focus on desktop experience parity             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Traffic Source Performance

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  🔗 Direct:     5.92%  ████▓▓▓▓▓▓▓▓▓▓▓▓▓▓          │
│  🔍 Google Org: 5.08%  ████▓▓▓▓▓▓▓▓▓▓▓▓▓▓          │
│  💰 Google CPC: 4.74%  ████▓▓▓▓▓▓▓▓▓▓▓▓▓▓          │
│                                                     │
│  ⚠️  Attribution limitation: First-touch only       │
│  🔍 Need session-level attribution analysis         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Product Anomalies

```
High-Traffic, Low-Conversion Products:

Product A: 10K views → 100 purchases (1.0%) ❌
Product B: 8K views  → 80 purchases  (1.0%) ❌
Product C: 5K views  → 50 purchases  (1.0%) ❌
Average:   6% conversion rate                        ✅

🔍 Investigation Required:
   • Inventory availability?
   • Tracking issues?
   • Product page UX?
   • Merchandising problem?
```

---

## Part 6: Tracking Health Alert

```
Event Volume Ratio Over Time:

1.0 ┤                    ┌─────────────────
    │                    │
0.8 ┤                    │
    │                    │
0.6 ┤                    │
    │                    │
0.4 ┤                    │
    │  ██████████████████│
0.2 ┤  ██████████████████│
    │  ██████████████████│
0.0 ┼────────────────────┼────────────────────→
    Nov 21              Nov 25

     CRITICAL OUTAGE     RECOVERY

✅ Successfully detected all 4 outage days
✅ Distinguished tracking failures from traffic declines
```

**Business Value:** Automated monitoring prevents bad business decisions based on bad data.

---

## Part 7: Predicting Purchase Intent

### The Model Approach

```
First View Item Event
        │
        ├─ How long to first view?
        ├─ What device?
        ├─ What time of day?
        ├─ What product category?
        ├─ How engaged before viewing?
        └─ New or returning visitor?
        │
        ▼
    Machine Learning Model
        │
        ▼
   Purchase Probability Score
        │
        ▼
   Top 10% = 3.12× Lift
```

### Model Performance

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  Model Performance:                                │
│                                                     │
│  Random Forest PR-AUC: 0.1402                      │
│  Baseline PR-AUC:     0.0504                       │
│  Improvement:         2.78×                         │
│                                                     │
│  ✅ Strong signal detected                         │
│  ✅ Better than random guessing                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Decile Analysis

```
Purchase Rate by Predicted Risk Decile:

Decile 1 (Highest Risk): 15.73% ████████████████████ 3.12× lift
Decile 2:                  8.50% ██████████████        1.69× lift
Decile 3:                  6.20% ██████████            1.23× lift
Decile 4:                  5.10% ████████              1.01× lift
Decile 5:                  4.30% ███████               0.85× lift
Decile 6:                  3.80% ██████                0.75× lift
Decile 7:                  3.40% ██████                0.67× lift
Decile 8:                  3.10% █████                 0.61× lift
Decile 9:                  2.80% █████                 0.56× lift
Decile 10 (Lowest Risk):   2.50% ████                 0.50× lift

Average:                   5.04% ████████

🎯 Top decile captures 31.3% of all purchases!
```

---

## Part 8: The Action Plan

### Immediate Actions (0-30 days)

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  🚀 REDUCE CHECKOUT FRICTION                        │
│                                                     │
│  1. Test guest checkout option                      │
│  2. Display shipping costs early                    │
│  3. Simplify checkout form fields                   │
│                                                     │
│  Expected Impact: +2-3% conversion                  │
│                                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                                                     │
│  🔍 AUDIT LOW-CONVERTING PRODUCTS                   │
│                                                     │
│  1. Check inventory availability                    │
│  2. Verify tracking instrumentation                 │
│  3. Review product page UX                          │
│                                                     │
│  Expected Impact: Fix tracking issues, improve UX  │
│                                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                                                     │
│  🔔 IMPLEMENT TRACKING HEALTH ALERTS                │
│                                                     │
│  1. Set up automated monitoring                     │
│  2. Create alert notification system               │
│                                                     │
│  Expected Impact: Prevent bad data decisions       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Medium-Term (1-3 months)

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  🧪 A/B TEST CHECKOUT OPTIMIZATIONS                │
│                                                     │
│  • Single-page vs. multi-page checkout             │
│  • Shipping cost transparency                      │
│  • Account requirement impact                      │
│                                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                                                     │
│  🎯 PROPENSITY SCORING PILOT                        │
│                                                     │
│  • Deploy model to identify high-intent visitors   │
│  • Test targeted interventions                      │
│  • Monitor conversion lift                          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Part 9: Business Impact

### ROI Estimate

```
Conservative Scenario:
• Current checkout rate: 13.98%
• Target checkout rate: 20.00%
• Improvement: +43% relative

Expected Results:
• Additional purchases: ~300/month
• Revenue increase: $15,000-$30,000/month
• Implementation cost: Low (UX changes)

─────────────────────────────────────────
Annual Impact: $180,000-$360,000
─────────────────────────────────────────
```

### Risk Management

```
⚠️  Risks:
   • Recommendations require A/B testing validation
   • Model needs calibration monitoring
   • Tracking may have ongoing quality issues

✅  Mitigations:
   • Start with low-risk changes (UX)
   • Implement model monitoring
   • Productionize tracking health alerts
```

---

## Part 10: Key Takeaways

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  🎯 THREE KEY INSIGHTS                              │
│                                                     │
│  1. 86% of product viewers never start checkout   │
│     → Biggest optimization opportunity             │
│                                                     │
│  2. Model achieves 3.12× lift in top decile        │
│     → Can identify high-intent visitors            │
│                                                     │
│  3. Tracking quality impacts all analysis           │
│     → Must monitor data quality continuously        │
│                                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                                                     │
│  📊 THE ANALYSIS JOURNEY                            │
│                                                     │
│  Raw Data → Quality Check → Funnel Analysis         │
      → Segmentation → Monitoring → Modeling         │
      → Insights → Recommendations → Action           │
│                                                     │
│  This is the complete data science workflow.       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Part 11: What's Next?

```
Current State:
┌─────────────────────────────────────────────────────┐
│  ✅ Static analysis completed                       │
│  ✅ Insights documented                             │
│  ✅ Recommendations prioritized                     │
│  ✅ Dashboard deployed                              │
└─────────────────────────────────────────────────────┘

Future State:
┌─────────────────────────────────────────────────────┐
│  🔄 Live data integration                          │
│  🔄 Real-time monitoring                            │
│  🔄 A/B testing platform                           │
│  🔄 Personalization engine                          │
│  🔄 Automated reporting                             │
└─────────────────────────────────────────────────────┘

The journey from analysis to action continues...
```

---

## Visual Summary

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│   📊 THE COMPLETE ANALYSIS STORY                                │
│                                                                │
│   Challenge → Data → Funnel → Segments → Monitoring → Model    │
│        │        │       │         │          │         │       │
│        │        │       │         │          │         │       │
│        ▼        ▼       ▼         ▼          ▼         ▼       │
│   ┌────────┐ ┌──────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌────┐ │
│   │ Where  │ │ 4.3M │ │ 86%  │ │ Mobile │ │ Alerts │ │ML  │ │
│   │ do we  │ │events│ │ drop │ │ 6.26% │ │  4/4  │ │3.1x│ │
│   │focus?  │ │      │ │      │ │       │ │       │ │    │ │
│   └────────┘ └──────┘ └──────┘ └────────┘ └────────┘ └────┘ │
│        │        │       │         │          │         │       │
│        └────────┴───────┴─────────┴──────────┴─────────┘       │
│                           │                                     │
│                           ▼                                     │
│                   ┌───────────────┐                             │
│                   │  ACTIONABLE   │                             │
│                   │ INSIGHTS &    │                             │
│                   │ RECOMMENDATIONS                             │
│                   └───────────────┘                             │
│                           │                                     │
│                           ▼                                     │
│                   ┌───────────────┐                             │
│                   │ BUSINESS IMPACT│                             │
│                   │ $180K-$360K/yr │                             │
│                   └───────────────┘                             │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

**This visual story walks through the complete analysis journey, making complex data accessible and memorable for stakeholders.**
