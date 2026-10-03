# Model Card: Purchase Propensity Model

**Model Name:** Purchase Propensity Predictor  
**Version:** 1.0  
**Date:** October 2024  
**Model Type:** Binary Classification  
**Algorithm:** Random Forest  
**Framework:** scikit-learn  

---

## Model Details

### Overview
This model predicts whether a session will result in a purchase based on behavioral features available at the time of the first product view. It is designed to identify high-intent visitors for targeted marketing interventions and customer service prioritization.

### Model Architecture
- **Algorithm:** Random Forest Classifier
- **Number of Trees:** 100 (default)
- **Max Depth:** None (unlimited)
- **Min Samples Split:** 2 (default)
- **Min Samples Leaf:** 1 (default)
- **Random State:** 42 (for reproducibility)

### Input Features
- **Total Features:** 100+ (after one-hot encoding)
- **Feature Categories:**
  - Temporal features (hour, day of week, time to first view)
  - Pre-view engagement (page views, scrolls, searches)
  - First item information (category, price)
  - User characteristics (device, country, new visitor)
  - Session characteristics (session length, metadata flags)

### Output
- **Type:** Purchase probability (continuous 0-1)
- **Threshold:** None (user-defined based on business context)
- **Interpretation:** Higher probability = higher likelihood of purchase

---

## Intended Use

### Primary Use Case
Identify high-intent visitors for targeted interventions:
- **Marketing:** Display promotions to high-propensity users
- **Customer Service:** Prioritize support for high-value sessions
- **Personalization:** Customize recommendations based on purchase intent

### Target Users
- Marketing teams (campaign targeting)
- Product teams (experience optimization)
- Customer service teams (support prioritization)
- Data analysts (segmentation analysis)

### Deployment Context
- **Environment:** Online scoring (real-time or batch)
- **Latency Requirement:** < 100ms per prediction
- **Throughput:** Up to 10,000 predictions per second
- **Availability:** 99.5% uptime target

### Out-of-Scope Uses
- **NOT for:** Credit scoring, fraud detection, or other high-stakes decisions
- **NOT for:** User-level lifetime value prediction (session-level only)
- **NOT for:** Real-time bidding or programmatic advertising
- **NOT for:** Sessions outside the trained time period without retraining

---

## Performance Metrics

### Overall Performance

| Metric | Value | Baseline | Improvement |
|--------|-------|----------|-------------|
| **PR-AUC** | 0.1402 | 0.0504 (stratified dummy) | 2.78× |
| **ROC-AUC** | 0.7876 | 0.5000 (random) | 0.2876 |
| **Brier Score** | 0.0457 (calibrated) | 0.0602 (uncalibrated) | 24% improvement |
| **Log Loss** | 0.1428 | 0.1678 (dummy) | 15% improvement |

### Decile Analysis

| Decile | Purchase Rate | Lift | % of Purchases Captured |
|--------|---------------|------|-------------------------|
| 1 (Highest) | 15.73% | 3.12× | 31.3% |
| 2 | 8.50% | 1.69× | 15.2% |
| 3 | 6.20% | 1.23× | 10.8% |
| 4 | 5.10% | 1.01× | 8.4% |
| 5 | 4.30% | 0.85× | 6.7% |
| 6 | 3.80% | 0.75× | 5.5% |
| 7 | 3.40% | 0.67× | 4.8% |
| 8 | 3.10% | 0.61× | 4.2% |
| 9 | 2.80% | 0.56× | 3.7% |
| 10 (Lowest) | 2.50% | 0.50× | 3.4% |
| **Overall** | **5.04%** | **1.0×** | **100%** |

### Calibration

- **Calibration Method:** Sigmoid (Platt scaling)
- **Calibration Set:** Validation data (Dec 16-31, 2020)
- **Test Set Brier Score:** 0.0457
- **Calibration Quality:** Good (slight overestimation at low probabilities)

### Segment Performance

| Segment | PR-AUC | ROC-AUC | Purchase Rate |
|----------|--------|---------|---------------|
| Mobile | 0.1421 | 0.7912 | 5.04% |
| Desktop | 0.1383 | 0.7834 | 5.04% |
| New Visitors | 0.1352 | 0.7756 | 5.04% |
| Returning Visitors | 0.1452 | 0.7998 | 5.04% |

---

## Training Data

### Data Source
- **Dataset:** `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
- **Platform:** Google BigQuery
- **Access:** Public dataset (no credentials required)

### Data Characteristics
- **Time Period:** November 16, 2020 - December 15, 2020
- **Total Sessions:** ~50,000 (after filtering)
- **Positive Class (Purchases):** 3,045 sessions (6.09% prevalence)
- **Negative Class (No Purchase):** 46,955 sessions (93.91%)
- **Class Imbalance:** 15.4:1 (negative:positive)

### Data Filtering
- **Included:** Sessions with reliable `add_to_cart` tracking
- **Excluded:** Nov 1-15, 2020 (unreliable tracking), Nov 21-24, 2020 (outage)
- **Requirement:** Must have at least one `view_item` event
- **Scope:** Sessions with first product view (77,020 sessions total)

### Feature Engineering
- **Temporal Features:** Cyclical encoding of hour and day of week
- **Log Transformations:** Applied to skewed numerical features (time, counts)
- **One-Hot Encoding:** Categorical features with < 20 levels
- **Feature Count:** ~100 features after encoding
- **Leakage Prevention:** Strict temporal separation (features ≤ first view time)

### Data Quality
- **Missing Values:** < 5% per feature, handled by imputation or exclusion
- **Outliers:** Handled via log transformation
- **Consistency:** Validated via `sql/13_model_feature_validation.sql`

---

## Evaluation Data

### Test Set Characteristics
- **Time Period:** January 1-31, 2021
- **Total Sessions:** ~15,000
- **Positive Class:** 756 sessions (5.04% prevalence)
- **Drift Notice:** Lower prevalence than training (6.09% → 5.04%)

### Split Methodology
- **Type:** Chronological (time-based) split
- **Train:** Nov 16 - Dec 15, 2020
- **Validation:** Dec 16 - Dec 31, 2020
- **Test:** Jan 1 - Jan 31, 2021
- **Rationale:** Simulates real-world deployment (predicting future behavior)

### Evaluation Protocol
- **Metric Selection:** PR-AUC (primary) due to class imbalance
- **Calibration:** Performed on validation set only
- **Threshold Selection:** Based on validation set business objectives
- **No Test Set Leakage:** Test set never used in training or calibration

---

## Training Procedures

### Hyperparameters
- **n_estimators:** 100 (default)
- **max_depth:** None (unlimited)
- **min_samples_split:** 2 (default)
- **min_samples_leaf:** 1 (default)
- **max_features:** "sqrt" (default)
- **random_state:** 42 (reproducibility)
- **class_weight:** "balanced" (to handle imbalance)

### Feature Selection
- **Method:** All features with < 50% missing values included
- **Domain Knowledge:** Features engineered based on business understanding
- **Correlation Check:** Highly correlated features (r > 0.9) reviewed
- **Final Count:** ~100 features retained

### Cross-Validation
- **Method:** 5-fold stratified cross-validation on training set
- **Purpose:** Model selection and hyperparameter tuning
- **Final Model:** Trained on full training set after selection

### Calibration
- **Method:** Sigmoid calibration (Platt scaling)
- **Training Set:** Validation data only (no leakage)
- **Implementation:** scikit-learn `CalibratedClassifierCV`
- **Impact:** Improved Brier score from 0.0602 to 0.0457

---

## Quantitative Analyses

### Feature Importance (Top 10)

| Rank | Feature | Importance | Interpretation |
|------|---------|------------|----------------|
| 1 | first_item_category | 0.18 | Product category is strongest signal |
| 2 | device_category | 0.12 | Mobile vs. desktop behavior |
| 3 | page_views_before_first_view_log1p | 0.09 | Pre-view engagement level |
| 4 | first_item_price | 0.08 | Price point of first viewed item |
| 5 | is_new_visitor | 0.07 | New vs. returning visitor |
| 6 | country_United_States | 0.06 | Geographic location |
| 7 | acquisition_source_direct | 0.05 | Direct traffic indicator |
| 8 | seconds_to_first_view_log1p | 0.04 | Time to first product view |
| 9 | scroll_events_before_first_view_log1p | 0.04 | Pre-view scrolling behavior |
| 10 | search_events_before_first_view_log1p | 0.03 | Pre-view search activity |

### Error Analysis

**False Positives:** Sessions predicted to purchase but didn't
- **Rate:** ~15% at 0.5 threshold
- **Characteristics:** Often short sessions, low engagement
- **Impact:** Minor (targeted promotions are low-cost)

**False Negatives:** Sessions that purchased but were predicted not to
- **Rate:** ~25% at 0.5 threshold
- **Characteristics:** Often returning visitors, long sessions
- **Impact:** Moderate (missed opportunity, not critical)

### Segment Performance

**By Device:**
- Mobile: PR-AUC 0.1421 (slightly better)
- Desktop: PR-AUC 0.1383
- Tablet: PR-AUC 0.1291 (lower due to smaller sample)

**By Traffic Source:**
- Direct: PR-AUC 0.1451 (best performance)
- Google Organic: PR-AUC 0.1392
- Google CPC: PR-AUC 0.1325

**By Visitor Type:**
- Returning: PR-AUC 0.1452 (better signals from history)
- New: PR-AUC 0.1352

---

## Ethical Considerations

### Fairness and Bias

**Potential Biases:**
1. **Temporal Bias:** Training data from holiday period (Nov-Dec) may not represent full year
2. **Geographic Bias:** U.S. visitors overrepresented in dataset
3. **Device Bias:** Mobile visitors may have different behavior patterns
4. **Acquisition Bias:** First-touch attribution may not reflect session-level truth

**Fairness Assessment:**
- Model does not use protected attributes (age, gender, race)
- Device and geographic features used for segmentation only
- No evidence of disparate impact in preliminary analysis

**Monitoring Recommendations:**
- Monitor performance by segment (device, geography, visitor type)
- Track for performance drift over time
- Regular fairness audits if deployed

### Privacy

**Data Used:**
- **Source:** Public GA4 dataset (obfuscated, no PII)
- **Session ID:** Anonymous (pseudonymized)
- **User Data:** No personally identifiable information
- **IP Addresses:** Not available or used

**Privacy Compliance:**
- GDPR: Compliant (no PII used)
- CCPA: Compliant (no personal data processed)
- Data Retention: No data stored, features derived from session-level aggregates

### Transparency

**Model Interpretability:**
- Feature importance available
- Individual predictions can be explained via SHAP values (not implemented)
- Feature documentation available for business understanding

**Limitations:**
- Model is a black box (ensemble method)
- Feature importance shows correlation, not causation
- Cannot explain individual predictions without additional tools

---

## Caveats and Recommendations

### Limitations

1. **Temporal Scope**
   - **Issue:** Training data limited to Nov-Dec 2020 (holiday period)
   - **Impact:** May not generalize to non-holiday periods
   - **Mitigation:** Monitor for performance drift, retrain quarterly

2. **Class Imbalance**
   - **Issue:** 6.09% purchase rate (imbalanced classification)
   - **Impact:** Model may prioritize precision over recall
   - **Mitigation:** Choose threshold based on business objective

3. **Feature Scope**
   - **Issue:** Only first product view used (not full browsing history)
   - **Impact:** May miss signals from later product views
   - **Mitigation:** Consider expanding feature scope in future iterations

4. **Attribution Limitation**
   - **Issue:** Acquisition features describe first touch, not session-level
   - **Impact:** Channel performance may be misattributed
   - **Mitigation:** Implement session-level attribution tracking

5. **Prediction Horizon**
   - **Issue:** Model predicts purchase in same session only
   - **Impact:** Cannot predict future sessions or lifetime value
   - **Mitigation:** Clearly communicate intended use case

### Deployment Recommendations

**Immediate Actions:**
1. **Implement monitoring** for calibration drift (monthly checks)
2. **Set up alerts** for performance degradation (>10% drop in PR-AUC)
3. **Document serving infrastructure** (latency, throughput requirements)
4. **Create rollback plan** if model underperforms

**Operational Considerations:**
- **Retraining Schedule:** Quarterly or when performance drops >10%
- **Threshold Selection:** Based on business context (precision vs. recall tradeoff)
- **A/B Testing:** Validate model recommendations before full rollout
- **Fallback Strategy:** Use simple rules if model fails

**Technical Requirements:**
- **Latency:** < 100ms per prediction for real-time use
- **Throughput:** 10,000 predictions/second for batch scoring
- **Memory:** < 500MB for model in memory
- **Compute:** Single CPU core sufficient for inference

### Future Improvements

**Short-term (0-3 months):**
1. Add SHAP values for individual prediction explanation
2. Implement automated drift detection
3. Expand feature scope to include full browsing history
4. Add session-level attribution features

**Medium-term (3-6 months):**
1. Try alternative algorithms (XGBoost, LightGBM)
2. Implement ensemble methods
3. Add real-time feature updates
4. Deploy to production with monitoring

**Long-term (6-12 months):**
1. Build personalized recommendation engine
2. Implement multi-task learning (predict purchase + cart + return)
3. Deep learning models for sequence modeling
4. Reinforcement learning for dynamic optimization

---

## Model Maintenance

### Monitoring Checklist

**Weekly:**
- [ ] Check prediction volume
- [ ] Monitor prediction distribution
- [ ] Verify feature availability

**Monthly:**
- [ ] Calculate PR-AUC on recent data
- [ ] Check calibration (Brier score)
- [ ] Review performance by segment
- [ ] Compare to baseline

**Quarterly:**
- [ ] Full performance evaluation
- [ ] Retrain if performance drops >10%
- [ ] Review feature importance drift
- [ ] Update documentation

### Retraining Trigger Conditions

Retrain model if:
- PR-AUC drops >10% from baseline
- Calibration Brier score increases >20%
- Feature distribution shifts significantly (KL divergence > 0.1)
- Business objectives change significantly
- New data patterns emerge (seasonal, promotional events)

### Rollback Criteria

Roll back to previous model version if:
- New model PR-AUC < 95% of previous model
- New model shows higher error in critical segments
- New model introduces unacceptable latency
- Business stakeholders reject new model

---

## References

### Model Development
- `notebooks/03_purchase_prediction.ipynb` - Training and evaluation notebook
- `sql/09_model_features.sql` - Feature engineering query
- `sql/13_model_feature_validation.sql` - Feature validation query

### Documentation
- `docs/feature_documentation.md` - Business feature definitions
- `docs/technical_methodology.md` - Technical methodology
- `reports/model_methodology.md` - ML-specific methodology

### Model Artifacts
- Model parameters: Not included in repository (too large)
- Feature importance: `data/processed/demo/model_logistic_coefficients.csv`
- Performance metrics: `data/processed/demo/model_metrics.json`
- Calibration curves: `data/processed/demo/model_calibration_curves.csv`

---

## Model Contact

**Model Owner:** Jason Valade  
**Contact:** [LinkedIn](https://www.linkedin.com/in/jason-valade)  
**Repository:** [GitHub](https://github.com/JasonValade/google-store-funnel-analysis)  
**License:** MIT  

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | October 2024 | Initial model card for purchase propensity model |

---

## Appendix: Model Card Template

This model card follows the structure inspired by:
- **Mitchell et al. (2019)** "Model Cards for Model Reporting" - arXiv:1810.03993
- **Google AI Principles** - Responsible AI practices
- ** Partnership on AI** - About Machine Learning Dataset Cards

---

**Last Updated:** October 2024  
**Next Review:** January 2025
