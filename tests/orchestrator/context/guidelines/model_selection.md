# Model Selection Guidelines

## Model Portfolio Requirements

**MS1.1** - **Model Diversity**
- **Check**: Multiple model types included in comparison
- **Method**: Verify at least 3 different algorithm families tested
- **Pass Criteria**: Includes linear, tree-based, and regularized models minimum
- **Severity**: WARNING

**MS1.2** - **Hyperparameter Optimization**
- **Check**: Systematic hyperparameter tuning performed
- **Method**: Grid search, random search, or Bayesian optimization within inner CV
- **Pass Criteria**: Hyperparameter search strategy documented and implemented
- **Severity**: WARNING

**MS1.3** - **Baseline Model Inclusion**
- **Check**: Simple baseline models included for comparison
- **Method**: Include logistic regression or other interpretable baseline
- **Pass Criteria**: At least one interpretable baseline model tested
- **Severity**: INFO

## Selection Criteria Hierarchy

**MS2.1** - **Clinical Safety Priority**
- **Check**: Clinical safety prioritized over statistical performance
- **Method**: Minimum sensitivity requirements for critical outcomes
- **Pass Criteria**: Safety constraints documented and enforced
- **Severity**: BLOCKER

**MS2.2** - **Statistical Significance Validation**
- **Check**: Model improvements are statistically significant
- **Method**: Statistical tests with multiple comparison correction
- **Pass Criteria**: Significant improvement over baseline (p<0.05 after correction)
- **Severity**: WARNING

**MS2.3** - **Confidence Interval Width Assessment**
- **Check**: Performance uncertainty quantified and acceptable
- **Method**: Bootstrap CI width analysis
- **Pass Criteria**: Primary metric CI width ≤0.1
- **Severity**: WARNING

**MS2.4** - **Interpretability Requirements**
- **Check**: Model interpretability adequate for clinical use
- **Method**: Feature importance analysis, clinical review
- **Pass Criteria**: Key clinical features identifiable and clinically sensible
- **Severity**: INFO

## Model Selection Decision Flow

1. **Safety Check**: Remove models failing clinical safety constraints
2. **Statistical Significance**: Test for significant improvements
3. **Uncertainty Assessment**: Evaluate CI widths
4. **Clinical Utility**: Assess interpretability and clinical fit
5. **Final Selection**: Choose best model meeting all criteria

## Required Model Comparison Metrics

### Performance Comparison Matrix
- Cross-validated AUC with CIs for all models
- Statistical significance tests between models
- Effect sizes (Cohen's d) for differences
- Clinical threshold performance for each model

### Model Characteristics Table
- Algorithm type and key hyperparameters
- Training time and computational requirements
- Interpretability score/assessment
- Feature importance rankings

## Regularization and Complexity

**MS3.1** - **Overfitting Prevention**
- **Check**: Appropriate regularization applied
- **Method**: Regularization parameters tuned via inner CV
- **Pass Criteria**: Gap between train and validation performance ≤0.05
- **Severity**: WARNING

**MS3.2** - **Model Complexity Justification**
- **Check**: Model complexity justified by performance improvement
- **Method**: Compare simple vs complex models with statistical tests
- **Pass Criteria**: Complex model significantly outperforms simpler alternatives
- **Severity**: INFO

## Final Model Requirements

**MS4.1** - **Single Model Selection**
- **Check**: One final model selected using predefined criteria
- **Method**: Apply selection hierarchy consistently
- **Pass Criteria**: Model selection rationale documented
- **Severity**: BLOCKER

**MS4.2** - **Model Serialization**
- **Check**: Final model properly saved for deployment
- **Method**: Model persistence with version control
- **Pass Criteria**: Model artifacts saved with metadata
- **Severity**: INFO
