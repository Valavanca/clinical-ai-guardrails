# Data Quality & Preparation Guidelines

## Data Quality Assessment Checklist

### Required Data Validation Checks

**DQ1.1** - **Missing Data Analysis**
- **Check**: Missing data patterns analyzed and documented
- **Method**: Count missing values per feature, identify patterns
- **Pass Criteria**: Missing data report exists with handling strategy
- **Severity**: BLOCKER

**DQ1.2** - **Class Balance Assessment**  
- **Check**: Class imbalance assessed and addressed appropriately
- **Method**: Calculate class distribution, assess impact
- **Pass Criteria**: Class distribution documented, resampling justified if used
- **Severity**: WARNING

**DQ1.3** - **Outlier Detection**
- **Check**: Outliers detected and clinically validated
- **Method**: Statistical outlier detection + clinical review
- **Pass Criteria**: Outlier analysis documented with clinical justification for inclusion/exclusion
- **Severity**: WARNING

**DQ1.4** - **Feature Distribution Validation**
- **Check**: Feature distributions examined for clinical plausibility
- **Method**: Distribution plots, clinical range validation
- **Pass Criteria**: Features fall within expected clinical ranges
- **Severity**: BLOCKER

**DQ1.5** - **Temporal Consistency**
- **Check**: Temporal trends identified and handled appropriately (if applicable)
- **Method**: Time series analysis, trend detection
- **Pass Criteria**: Temporal effects documented and accounted for
- **Severity**: WARNING

## Sample Size Requirements

**DQ2.1** - **Minimum Sample Size**
- **Check**: Sample size meets statistical requirements
- **Method**: Power analysis, events per variable calculation
- **Pass Criteria**: ≥10 events per predictor variable, or power analysis justifies smaller sample
- **Severity**: BLOCKER

**DQ2.2** - **Train/Test Split Preservation**
- **Check**: Predefined train/test splits are maintained
- **Method**: Verify no data leakage between splits
- **Pass Criteria**: Original splits preserved, no temporal leakage
- **Severity**: BLOCKER

## Required Artifacts

- Missing data analysis report
- Class distribution summary
- Outlier detection results
- Feature distribution plots
- Sample size calculation/justification
- Train/test split documentation

## Clinical Context Integration

**DQ3.1** - **Clinical Feature Validation**
- **Check**: All features have clinical justification
- **Method**: Clinical expert review of feature selection
- **Pass Criteria**: Each feature mapped to clinical rationale
- **Severity**: WARNING

**DQ3.2** - **Data Anonymization Verification**
- **Check**: Patient data properly anonymized
- **Method**: PHI scanning, anonymization audit
- **Pass Criteria**: No identifiable information present
- **Severity**: BLOCKER
