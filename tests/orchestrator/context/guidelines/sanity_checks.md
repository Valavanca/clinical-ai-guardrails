# Methodological Sanity Checks

## Data Leakage Detection

**SC1.1** - **Temporal Leakage**
- **Check**: No future information used to predict past events
- **Method**: Verify temporal ordering in data splits
- **Pass Criteria**: All features available before prediction time
- **Severity**: BLOCKER

**SC1.2** - **Target Leakage**
- **Check**: No features contain information about target variable
- **Method**: Feature correlation analysis with target
- **Pass Criteria**: No features with r>0.95 correlation with target
- **Severity**: BLOCKER

**SC1.3** - **Group Leakage**
- **Check**: Related samples properly separated between train/test
- **Method**: Check for patient/group overlap between splits
- **Pass Criteria**: No subject appears in both train and test sets
- **Severity**: BLOCKER

## Cross-Validation Integrity

**SC2.1** - **CV Fold Independence**
- **Check**: CV folds are properly independent
- **Method**: Verify no data sharing between folds
- **Pass Criteria**: Independent random seeds, no overlap
- **Severity**: BLOCKER

**SC2.2** - **Preprocessing Within Folds**
- **Check**: Data preprocessing done within each CV fold
- **Method**: Check normalization, scaling applied per fold
- **Pass Criteria**: No preprocessing on full dataset before CV
- **Severity**: BLOCKER

**SC2.3** - **Hyperparameter Selection Bias**
- **Check**: Hyperparameter tuning not biased by test performance
- **Method**: Verify inner CV used for hyperparameter selection
- **Pass Criteria**: Test set never used for model selection
- **Severity**: BLOCKER

## Label and Target Validation

**SC3.1** - **Label Consistency**
- **Check**: Labels consistent across train/test splits
- **Method**: Verify label distributions and encoding
- **Pass Criteria**: Same label encoding and distribution patterns
- **Severity**: BLOCKER

**SC3.2** - **Missing Label Handling**
- **Check**: Missing labels handled appropriately
- **Method**: Check for unlabeled samples in training
- **Pass Criteria**: No missing labels in training, proper handling in test
- **Severity**: WARNING

**SC3.3** - **Class Balance Validation**
- **Check**: Severe class imbalance identified and addressed
- **Method**: Calculate class ratios, assess impact
- **Pass Criteria**: Class imbalance <10:1 or proper handling documented
- **Severity**: WARNING

## Feature Engineering Validation

**SC4.1** - **Feature Scaling Consistency**
- **Check**: Consistent feature scaling between train/test
- **Method**: Verify scaling parameters computed on train only
- **Pass Criteria**: Test set scaled using train set parameters
- **Severity**: BLOCKER

**SC4.2** - **Feature Selection Bias**
- **Check**: Feature selection not biased by test set
- **Method**: Verify feature selection done within CV
- **Pass Criteria**: No feature selection using full dataset
- **Severity**: BLOCKER

**SC4.3** - **Categorical Encoding Consistency**
- **Check**: Categorical variables encoded consistently
- **Method**: Check encoding dictionaries consistent across splits
- **Pass Criteria**: Same encoding scheme applied to train/test
- **Severity**: WARNING

## Model Training Validation

**SC5.1** - **Random Seed Management**
- **Check**: Random seeds properly managed for reproducibility
- **Method**: Verify seeds set for all random processes
- **Pass Criteria**: All random processes seeded, seeds documented
- **Severity**: INFO

**SC5.2** - **Overfitting Detection**
- **Check**: Signs of overfitting identified
- **Method**: Compare train vs validation performance
- **Pass Criteria**: Train-validation gap <0.1 for primary metric
- **Severity**: WARNING

**SC5.3** - **Convergence Validation**
- **Check**: Model training converged properly
- **Method**: Check training curves, convergence criteria
- **Pass Criteria**: Training converged, no early stopping issues
- **Severity**: WARNING

## Common Anti-Patterns

**SC6.1** - **Test Set Peeking**
- **Check**: Test set not used during model development
- **Method**: Audit all code for test set access
- **Pass Criteria**: Test set only accessed for final evaluation
- **Severity**: BLOCKER

**SC6.2** - **Multiple Testing Without Correction**
- **Check**: Multiple model comparisons properly corrected
- **Method**: Check for multiple testing correction
- **Pass Criteria**: Bonferroni or FDR correction applied
- **Severity**: WARNING

**SC6.3** - **Cherry-Picking Results**
- **Check**: All experimental results reported
- **Method**: Check for selective reporting
- **Pass Criteria**: All experiments documented, negative results included
- **Severity**: WARNING
