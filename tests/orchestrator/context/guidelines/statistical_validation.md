# Statistical Validation Guidelines

## Cross-Validation Requirements

**SV1.1** - **Nested Cross-Validation Implementation**
- **Check**: Proper nested CV with independent random seeds
- **Method**: Verify outer/inner CV use different seeds, no data leakage
- **Pass Criteria**: Nested CV correctly implemented with documented seed strategy
- **Severity**: BLOCKER

**SV1.2** - **Stratification Enforcement**
- **Check**: Class proportions maintained in all CV folds
- **Method**: Check class distribution across folds
- **Pass Criteria**: Class proportions consistent across folds (±5%)
- **Severity**: BLOCKER

**SV1.3** - **Feature Selection Within Folds**
- **Check**: Feature selection performed within each CV fold
- **Method**: Verify feature selection code placement
- **Pass Criteria**: No feature selection on full dataset before CV
- **Severity**: BLOCKER

## Statistical Testing Framework

**SV2.1** - **Model Comparison Testing**
- **Check**: Statistical tests used for model comparison
- **Method**: Paired t-test or Wilcoxon signed-rank test
- **Pass Criteria**: p-values reported with appropriate test selection justification
- **Severity**: WARNING

**SV2.2** - **Multiple Comparison Correction**
- **Check**: Multiple testing correction applied when comparing >2 models
- **Method**: Bonferroni or FDR correction
- **Pass Criteria**: Corrected p-values reported for multiple comparisons
- **Severity**: WARNING

**SV2.3** - **Effect Size Reporting**
- **Check**: Cohen's d or equivalent effect size reported
- **Method**: Calculate standardized effect size
- **Pass Criteria**: Effect size ≥0.2 for small, ≥0.5 for medium, ≥0.8 for large effects
- **Severity**: INFO

## Confidence Interval Requirements

**SV3.1** - **Bootstrap Confidence Intervals**
- **Check**: Performance metrics include bootstrap CIs
- **Method**: Non-parametric bootstrap with ≥1000 samples
- **Pass Criteria**: 95% CI width ≤0.1 for primary metrics
- **Severity**: WARNING

**SV3.2** - **Wilson Score Intervals**
- **Check**: Binomial proportions use Wilson intervals
- **Method**: Wilson score CI instead of normal approximation
- **Pass Criteria**: Wilson intervals used for sensitivity/specificity
- **Severity**: INFO

## Required Statistical Computations

### Primary Metrics (All Required)
- Area Under ROC Curve (AUC) with 95% CI
- Sensitivity with 95% CI  
- Specificity with 95% CI
- Positive Predictive Value with 95% CI
- Negative Predictive Value with 95% CI

### Secondary Metrics (Recommended)
- F1-Score with 95% CI
- Cohen's Kappa
- Calibration metrics (Brier score, calibration slope)

## Threshold Optimization

**SV4.1** - **Clinical Threshold Justification**
- **Check**: Decision thresholds optimized for clinical objectives
- **Method**: ROC analysis, cost-sensitive optimization, or clinical constraints
- **Pass Criteria**: Threshold selection method documented and clinically justified
- **Severity**: WARNING

**SV4.2** - **Constraint Satisfaction**
- **Check**: Clinical constraints (min sensitivity/specificity) met
- **Method**: Verify threshold meets predetermined clinical requirements
- **Pass Criteria**: All clinical constraints satisfied at chosen threshold
- **Severity**: BLOCKER

## Test Set Validation

**SV5.1** - **Holdout Test Set Evaluation**
- **Check**: Final model evaluated on truly held-out test set
- **Method**: Single evaluation on test set after model selection
- **Pass Criteria**: Test set performance reported, consistent with CV estimates
- **Severity**: BLOCKER

**SV5.2** - **Performance Consistency Check**
- **Check**: Test set performance within expected range of CV estimates
- **Method**: Compare test vs CV performance, check if within CI
- **Pass Criteria**: Test performance within 95% CI of CV estimates
- **Severity**: WARNING
