"""
Statistical validation tools for clinical AI.
Composable, testable utilities focused on clinical requirements.
"""

from __future__ import annotations
import numpy as np
from typing import Dict, List, Union, Tuple, Any, Optional
from dataclasses import dataclass
from scipy import stats
from scipy.stats import norm
from sklearn.metrics import roc_auc_score, confusion_matrix, roc_curve

from smolagents import Tool

ArrayLike = Union[List[float], np.ndarray]


@dataclass 
class ValidationResult:
    """Standardized validation result."""
    check_id: str
    status: str  # PASS, FAIL, SKIP, ERROR
    message: str
    evidence: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None


@dataclass
class StatisticalResult:
    """Standardized statistical computation result."""
    metric_name: str
    value: float
    confidence_interval: Optional[Dict[str, Union[float, int]]] = None
    method: str = ""
    sample_size: int = 0
    metadata: Optional[Dict[str, Any]] = None


class StatisticalTestTool(Tool):
    """Performs statistical tests for model comparison with clinical requirements."""
    
    name = "statistical_test"
    description = "Performs statistical tests for model comparison (t-test, Wilcoxon)"
    inputs = {
        "scores_a": {
            "type": "array",
            "description": "Performance scores from model A (e.g., CV fold AUCs)"
        },
        "scores_b": {
            "type": "array", 
            "description": "Performance scores from model B (paired with scores_a)"
        },
        "test_type": {
            "type": "string",
            "description": "Statistical test: 'paired_ttest' or 'wilcoxon'",
            "default": "wilcoxon",
            "nullable": False
        },
        "alpha": {
            "type": "number",
            "description": "Significance level",
            "default": 0.05,
            "nullable": False
        }
    }
    output_type = "object"
    
    def forward(self, scores_a: ArrayLike, scores_b: ArrayLike, 
               test_type: str = "wilcoxon", alpha: float = 0.05) -> Dict[str, Any]:
        """Perform statistical test for model comparison."""
        
        scores_a = np.asarray(scores_a)
        scores_b = np.asarray(scores_b)
        
        if scores_a.shape != scores_b.shape:
            raise ValueError("Score arrays must have same shape")
        
        n = len(scores_a)
        
        # Perform test
        if test_type == "paired_ttest":
            statistic, p_value = stats.ttest_rel(scores_a, scores_b)
            test_name = "Paired t-test"
        elif test_type == "wilcoxon":
            statistic, p_value = stats.wilcoxon(scores_a, scores_b)
            test_name = "Wilcoxon signed-rank test"
        else:
            raise ValueError(f"Unknown test type: {test_type}")
        
        # Effect size
        diff = scores_a - scores_b
        effect_size = np.mean(diff) / np.std(diff, ddof=1) if np.std(diff) > 0 else 0
        
        # Clinical significance (arbitrary threshold of 0.02 AUC difference)
        clinical_significance = abs(np.mean(diff)) >= 0.02
        
        return {
            "test_name": test_name,
            "statistic": float(statistic),
            "p_value": float(p_value),
            "significant": p_value < alpha,
            "effect_size": float(effect_size),
            "mean_difference": float(np.mean(diff)),
            "clinical_significance": clinical_significance,
            "sample_size": n
        }


class MultipleTestingCorrectionTool(Tool):
    """Applies multiple testing correction for model comparisons."""
    
    name = "multiple_testing_correction"
    description = "Apply Bonferroni or FDR correction for multiple comparisons"
    inputs = {
        "p_values": {
            "type": "array",
            "description": "Array of uncorrected p-values"
        },
        "method": {
            "type": "string", 
            "description": "Correction method: 'bonferroni' or 'fdr'",
            "default": "bonferroni",
            "nullable": False
        },
        "alpha": {
            "type": "number",
            "description": "Overall significance level",
            "default": 0.05,
            "nullable": False
        }
    }
    output_type = "object"
    
    def forward(self, p_values: ArrayLike, method: str = "bonferroni", 
               alpha: float = 0.05) -> Dict[str, Any]:
        """Apply multiple testing correction."""
        
        from statsmodels.stats.multitest import multipletests
        
        p_values = np.asarray(p_values)
        
        if method == "bonferroni":
            rejected, p_corrected, alpha_sidak, alpha_bonf = multipletests(
                p_values, alpha=alpha, method='bonferroni'
            )
            correction_name = "Bonferroni"
        elif method == "fdr":
            rejected, p_corrected, alpha_sidak, alpha_bonf = multipletests(
                p_values, alpha=alpha, method='fdr_bh'
            )
            correction_name = "Benjamini-Hochberg FDR"
        else:
            raise ValueError(f"Unknown correction method: {method}")
        
        return {
            "correction_method": correction_name,
            "original_p_values": p_values.tolist(),
            "corrected_p_values": p_corrected.tolist(),
            "rejected": rejected.tolist(),
            "significant_count": int(np.sum(rejected)),
            "corrected_alpha": float(alpha_bonf)
        }


class ClinicalMetricsTool(Tool):
    """Computes clinical performance metrics with confidence intervals calculated with the Wilson score method."""

    name = "clinical_metrics"
    description = "Compute clinical metrics (sensitivity, specificity, PPV, NPV) with CIs"
    inputs = {
        "y_true": {
            "type": "array",
            "description": "True binary labels"
        },
        "y_pred": {
            "type": "array",
            "description": "Predicted binary labels or probabilities"
        },
        "threshold": {
            "type": "number",
            "description": "Decision threshold for probabilities",
            "default": 0.5,
            "nullable": False
        },
        "alpha": {
            "type": "number",
            "description": "Significance level for CIs",
            "default": 0.05,
            "nullable": False
        }
    }
    output_type = "object"
    
    def forward(self, y_true: ArrayLike, y_pred: ArrayLike,
                threshold: float = 0.5, alpha: float = 0.05) -> Dict[str, Any]:
        """Compute clinical metrics with confidence intervals."""
        y_true = np.asarray(y_true, dtype=int)
        y_pred = np.asarray(y_pred)
        
        # Convert probabilities to binary predictions if needed
        if np.max(y_pred) <= 1.0 and np.min(y_pred) >= 0.0 and len(np.unique(y_pred)) > 2:
            y_pred_binary = (y_pred >= threshold).astype(int)
        else:
            y_pred_binary = y_pred.astype(int)
        
        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred_binary).ravel()
        
        # Calculate metrics
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
        npv = tn / (tn + fn) if (tn + fn) > 0 else 0
        
        # Calculate confidence intervals
        def wilson_ci(x, n, alpha=0.05):
            """Wilson score confidence interval."""
            from scipy.stats import norm
            z = norm.ppf(1 - alpha/2)
            center = (x + z**2/2) / (n + z**2)
            width = z * np.sqrt((x*(n-x)/n + z**2/4) / (n + z**2))
            return max(0, center - width), min(1, center + width)
        
        results = {}
        
        # Sensitivity CI
        if (tp + fn) > 0:
            sens_ci = wilson_ci(tp, tp + fn, alpha)
            results["sensitivity"] = {
                "value": sensitivity,
                "ci_lower": sens_ci[0],
                "ci_upper": sens_ci[1],
                "method": "Wilson score"
            }
        
        # Specificity CI  
        if (tn + fp) > 0:
            spec_ci = wilson_ci(tn, tn + fp, alpha)
            results["specificity"] = {
                "value": specificity,
                "ci_lower": spec_ci[0], 
                "ci_upper": spec_ci[1],
                "method": "Wilson score"
            }
        
        # PPV CI
        if (tp + fp) > 0:
            ppv_ci = wilson_ci(tp, tp + fp, alpha)
            results["ppv"] = {
                "value": ppv,
                "ci_lower": ppv_ci[0],
                "ci_upper": ppv_ci[1],
                "method": "Wilson score"
            }
        
        # NPV CI
        if (tn + fn) > 0:
            npv_ci = wilson_ci(tn, tn + fn, alpha)
            results["npv"] = {
                "value": npv,
                "ci_lower": npv_ci[0],
                "ci_upper": npv_ci[1],
                "method": "Wilson score"
            }
        
        # Add confusion matrix and sample size
        results["confusion_matrix"] = {
            "tn": int(tn), "fp": int(fp), 
            "fn": int(fn), "tp": int(tp)
        }
        results["sample_size"] = len(y_true)
        results["threshold"] = threshold
        
        return results


class ClinicalThresholdTool(Tool):
    """Optimizes decision thresholds for clinical constraints."""
    
    name = "clinical_threshold"
    description = "Find optimal threshold given clinical constraints"
    inputs = {
        "y_true": {
            "type": "array",
            "description": "True binary labels"
        },
        "y_proba": {
            "type": "array", 
            "description": "Predicted probabilities"
        },
        "min_sensitivity": {
            "type": "number",
            "description": "Minimum required sensitivity",
            "default": None,
            "nullable": False
        },
        "min_specificity": {
            "type": "number",
            "description": "Minimum required specificity", 
            "default": None,
            "nullable": False
        },
        "cost_fn": {
            "type": "number",
            "description": "Cost of false negative",
            "default": 1,
            "nullable": False
        },
        "cost_fp": {
            "type": "number", 
            "description": "Cost of false positive",
            "default": 1,
            "nullable": False
        }
    }
    output_type = "object"
    
    def forward(self, y_true: ArrayLike, y_proba: ArrayLike,
               min_sensitivity: Optional[float] = None,
               min_specificity: Optional[float] = None,
               cost_fn: float = 1, cost_fp: float = 1) -> Dict[str, Any]:
        """Find optimal threshold for clinical use."""
        
        y_true = np.asarray(y_true)
        y_proba = np.asarray(y_proba)
        
        fpr, tpr, thresholds = roc_curve(y_true, y_proba)
        specificity = 1 - fpr
        
        results = {}
        
        # Youden's J statistic (balanced)
        j_scores = tpr + specificity - 1
        youden_idx = np.argmax(j_scores)
        results["youden"] = {
            "threshold": float(thresholds[youden_idx]),
            "sensitivity": float(tpr[youden_idx]),
            "specificity": float(specificity[youden_idx]),
            "j_score": float(j_scores[youden_idx])
        }
        
        # Cost-sensitive threshold
        costs = []
        for i, threshold in enumerate(thresholds):
            # Estimate prevalence from data
            prevalence = np.mean(y_true)
            
            # Expected cost calculation
            cost = (prevalence * (1 - tpr[i]) * cost_fn + 
                   (1 - prevalence) * fpr[i] * cost_fp)
            costs.append(cost)
        
        cost_optimal_idx = np.argmin(costs)
        results["cost_optimal"] = {
            "threshold": float(thresholds[cost_optimal_idx]),
            "sensitivity": float(tpr[cost_optimal_idx]),
            "specificity": float(specificity[cost_optimal_idx]),
            "expected_cost": float(costs[cost_optimal_idx])
        }
        
        # Constrained threshold
        if min_sensitivity is not None or min_specificity is not None:
            valid_mask = np.ones(len(thresholds), dtype=bool)
            
            if min_sensitivity is not None:
                valid_mask &= (tpr >= min_sensitivity)
            if min_specificity is not None:
                valid_mask &= (specificity >= min_specificity)
            
            if np.any(valid_mask):
                valid_indices = np.where(valid_mask)[0]
                # Among valid thresholds, pick the one with best Youden's J
                valid_j_scores = j_scores[valid_mask]
                best_valid_idx = valid_indices[np.argmax(valid_j_scores)]
                
                results["constrained"] = {
                    "threshold": float(thresholds[best_valid_idx]),
                    "sensitivity": float(tpr[best_valid_idx]),
                    "specificity": float(specificity[best_valid_idx]),
                    "constraints_met": True
                }
            else:
                results["constrained"] = {
                    "threshold": None,
                    "constraints_met": False,
                    "message": "No threshold satisfies clinical constraints"
                }
        
        return results


class PerformanceValidatorTool(Tool):
    """Validates performance against clinical requirements."""
    
    name = "performance_validator"
    description = "Validate model performance against clinical requirements"
    inputs = {
        "metrics": {
            "type": "object",
            "description": "Dictionary of performance metrics with CIs"
        },
        "requirements": {
            "type": "object", 
            "description": "Clinical requirements (min_auc, max_ci_width, etc.)"
        }
    }
    output_type = "array"
    
    def forward(self, metrics: Dict[str, Any], 
               requirements: Dict[str, Any]) -> List[ValidationResult]:
        """Validate performance against requirements."""
        
        results = []
        
        if "min_auc" in requirements and "auc" in metrics:
            auc_value = metrics["auc"].get("value", 0)
            min_auc = requirements["min_auc"]
            
            status = "PASS" if auc_value >= min_auc else "FAIL"
            message = f"AUC {auc_value:.3f} {'meets' if status == 'PASS' else 'below'} minimum {min_auc}"
            
            results.append(ValidationResult(
                check_id="MS2.1",
                status=status,
                message=message,
                evidence={"auc": auc_value, "requirement": min_auc}
            ))
        
        if "max_ci_width" in requirements:
            max_width = requirements["max_ci_width"]
            
            for metric_name, metric_data in metrics.items():
                if isinstance(metric_data, dict) and "ci_lower" in metric_data and "ci_upper" in metric_data:
                    width = metric_data["ci_upper"] - metric_data["ci_lower"]
                    status = "PASS" if width <= max_width else "FAIL"
                    message = f"{metric_name} CI width {width:.3f} {'acceptable' if status == 'PASS' else 'too wide'}"
                    
                    results.append(ValidationResult(
                        check_id=f"SV3.1_{metric_name}",
                        status=status,
                        message=message,
                        evidence={"ci_width": width, "requirement": max_width}
                    ))
        
        if "min_sensitivity" in requirements and "sensitivity" in metrics:
            sens_value = metrics["sensitivity"].get("value", 0)
            min_sens = requirements["min_sensitivity"]
            
            status = "PASS" if sens_value >= min_sens else "FAIL"
            message = f"Sensitivity {sens_value:.3f} {'meets' if status == 'PASS' else 'below'} minimum {min_sens}"
            
            results.append(ValidationResult(
                check_id="CI2.1",
                status=status,
                message=message,
                evidence={"sensitivity": sens_value, "requirement": min_sens}
            ))
        
        return results


class CohensDTool(Tool):
    name = "cohens_d"
    description = """
    Compute Cohen's d effect size between two samples.
    Cohen's d is a standardized measure of effect size that represents the difference 
    between two groups in terms of standard deviation units.
    """
    inputs = {
        "x": {
            "type": "array", 
            "description": "Metric scores from model A. For paired design, observations must correspond positionally with y."
        },
        "y": {
            "type": "array",
            "description": "Metric scores from model B. For paired design, observations must correspond positionally with x."
        },
        "paired": {
            "type": "boolean",
            "description": "If True, compute paired Cohen's d. If False, compute independent-samples Cohen's d.",
            "default": False,
            "nullable": False
        },
        "ddof": {
            "type": "integer",
            "description": "Delta degrees-of-freedom for variance calculation. A value of 1 yields the unbiased sample estimate.",
            "default": 1,
            "nullable": False
        },
        "nan_policy": {
            "type": "string",
            "description": "How to handle NaNs: 'raise' (throw error) or 'omit' (remove NaNs).",
            "default": "raise",
            "nullable": False
        }
    }
    output_type = "number"
    
    def forward(
        self,
        x: ArrayLike,
        y: ArrayLike,
        *,
        paired: bool = False,
        ddof: int = 1,
        nan_policy: str = "raise",
    ) -> float:
        """Compute Cohen's *d* effect size between two samples.
        
        Args:
            x: Metric scores from model *A*. For paired design, observations must 
                correspond positionally with y.
            y: Metric scores from model *B*. For paired design, observations must
                correspond positionally with x.
            paired: If True, compute **paired** Cohen's *d* (mean of differences divided
                by the standard deviation of differences). If False, compute 
                **independent‑samples** Cohen's *d* using the pooled standard
                deviation (equal variances assumed). Defaults to False.
            ddof: Delta degrees‑of‑freedom passed to numpy.ndarray.std/var.
                A value of 1 (the default) yields the unbiased sample estimate.
                Defaults to 1.
            nan_policy: How to handle NaNs. Options:
                'raise': Throw ValueError if x or y contains NaN.
                'omit': Remove NaNs pairwise if paired is True, otherwise remove
                    NaNs element‑wise from each sample independently.
                Defaults to "raise".
        
        Returns:
            Cohen's *d* effect size.
            
        Notes:
            *Paired design*
                For *n* paired observations, we compute::
        
                    d = mean(x - y) / std(x - y, ddof=ddof)
        
            *Independent samples*
                Let n_x and n_y be sample sizes and var denote the
                unbiased sample variance. The pooled standard deviation is::
        
                    s_pooled = sqrt(((n_x - 1) * var(x) + (n_y - 1) * var(y)) /
                                    (n_x + n_y - 2))
        
                Then::
        
                    d = (mean(x) - mean(y)) / s_pooled
        
        References:
            Cohen, J. (1988). *Statistical Power Analysis for the Behavioral
            Sciences* (2nd ed.). Lawrence Erlbaum Associates.
        """

        # -- Convert inputs
        x_arr = np.asarray(x, dtype=float)
        y_arr = np.asarray(y, dtype=float)

        # -- NaN handling
        if nan_policy == "omit":
            if paired:
                mask = ~(np.isnan(x_arr) | np.isnan(y_arr))
                x_arr, y_arr = x_arr[mask], y_arr[mask]
            else:
                x_arr = x_arr[~np.isnan(x_arr)]
                y_arr = y_arr[~np.isnan(y_arr)]
        elif nan_policy == "raise":
            if np.isnan(x_arr).any() or np.isnan(y_arr).any():
                raise ValueError("NaN present in input and nan_policy='raise'")
        else:
            raise ValueError("nan_policy must be 'raise' or 'omit'")

        # -- Validation
        if paired and x_arr.shape != y_arr.shape:
            raise ValueError("For paired design, x and y must be the same length")

        if x_arr.size < 2 or y_arr.size < 2:
            raise ValueError("Need at least two observations per group")

        # -- Computation
        if paired:
            diff = x_arr - y_arr
            sd_diff = diff.std(ddof=ddof)
            if sd_diff == 0:
                raise ValueError("Standard deviation of differences is zero")
            return diff.mean() / sd_diff

        # -- Independent samples
        n_x, n_y = x_arr.size, y_arr.size
        var_x = x_arr.var(ddof=ddof) # unbiased sample variance
        var_y = y_arr.var(ddof=ddof) # unbiased sample variance
        s_pooled = np.sqrt(((n_x - 1) * var_x + (n_y - 1) * var_y) / (n_x + n_y - 2))
        if s_pooled == 0:
            raise ValueError("Pooled standard deviation is zero; likely identical data")
        return (x_arr.mean() - y_arr.mean()) / s_pooled
    

class BootstrapMetricTool(Tool):
    name = "bootstrap_metric"
    description = """
    Non‑parametric bootstrap confidence interval for an arbitrary prediction metric.
    Provides statistical confidence intervals for any metric function that takes
    true labels and predictions as inputs.
    """
    inputs = {
        "metric_fn": {
            "type": "object", 
            "description": "Metric function that takes y_true and y_pred and returns a scalar value (e.g. sklearn.metrics.f1_score)."
        },
        "y_true": {
            "type": "array",
            "description": "Ground‑truth labels. Must be broadcastable to the same shape as y_pred."
        },
        "y_pred": {
            "type": "array",
            "description": "Corresponding predictions. Must be broadcastable to the same shape as y_true."
        },
        "B": {
            "type": "integer",
            "description": "Number of bootstrap resamples.",
            "default": 1000,
            "nullable": False
        },
        "alpha": {
            "type": "number",
            "description": "Significance level for the two‑sided interval.",
            "default": 0.05,
            "nullable": False
        },
        "seed": {
            "type": "integer",
            "description": "Seed or pre‑existing RNG for reproducibility. If None, a fresh generator is created from OS entropy.",
            "default": None,
            "nullable": True
        }
    }
    output_type = "array"
    
    def forward(
        self,
        metric_fn: Any,
        y_true: ArrayLike,
        y_pred: ArrayLike,
        B: int = 1000,
        alpha: float = 0.05,
        seed: Union[int, np.random.Generator, None] = None,
    ) -> Tuple[float, float]:
        """Non‑parametric bootstrap confidence interval for an arbitrary prediction metric.
        
        Args:
            metric_fn: Metric function that takes *y_true* and *y_pred* and returns a scalar
                value (e.g. `sklearn.metrics.f1_score`).
            y_true: Ground‑truth labels. Must be broadcastable to the same shape as y_pred.
            y_pred: Corresponding predictions. Must be broadcastable to the same shape as y_true.
            B: Number of bootstrap resamples. Defaults to 1000.
            alpha: Significance level for the two‑sided interval. Defaults to 0.05.
            seed: Seed or pre‑existing RNG for reproducibility. If None, a fresh
                generator is created from OS entropy. Defaults to None.
                
        Returns:
            Percentile interval of the bootstrapped metric values.
            
        Raises:
            ValueError: If input shapes differ, *B* ≤ 0, or *alpha* not in *(0, 1)*.
        """
        # --- Input validation & coercion
        if B <= 0:
            raise ValueError("B must be a positive integer")
        if not (0.0 < alpha < 1.0):
            raise ValueError("alpha must lie strictly between 0 and 1")

        y_true_arr = np.asarray(y_true)
        y_pred_arr = np.asarray(y_pred)
        if y_true_arr.shape != y_pred_arr.shape:
            raise ValueError("y_true and y_pred must have identical shapes")

        n = y_true_arr.shape[0]

        # --- RNG setup
        rng = seed if isinstance(seed, np.random.Generator) else np.random.default_rng(seed)

        # --- Bootstrap resampling
        metrics = np.empty(B, dtype=float)
        for i in range(B):
            idx = rng.integers(0, n, n, endpoint=False)
            metrics[i] = metric_fn(y_true_arr[idx], y_pred_arr[idx])

        lo, hi = np.percentile(metrics, [100 * alpha / 2.0, 100 * (1.0 - alpha / 2.0)])
        return float(lo), float(hi)
    

class WilsonCITool(Tool):
    name = "wilson_ci"
    description = """
    Compute the two‑sided Wilson score confidence interval for a binomial proportion.
    The Wilson interval generally has better coverage properties than the normal 
    approximation, especially for small sample sizes or extreme proportions.
    """
    inputs = {
        "x": {
            "type": "integer",
            "description": "Number of observed successes.",
        },
        "n": {
            "type": "integer", 
            "description": "Total number of Bernoulli trials. Must be > 0.",
        },
        "alpha": {
            "type": "number",
            "description": "Significance level (0 < alpha < 1). The returned interval has nominal coverage of (1 − alpha).",
            "default": 0.05,
            "nullable": False
        }
    }
    output_type = "array"
    
    def forward(self, x: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
        """Compute the two‑sided Wilson score confidence interval for a binomial proportion.
        
        Args:
            x: Number of observed *successes*.
            n: Total number of Bernoulli trials. Must be > 0.
            alpha: Significance level (*0 < alpha < 1*). The returned interval has
                nominal coverage of *(1 − alpha)*. Defaults to 0.05.
                
        Returns:
            Tuple containing lower and upper bounds of the Wilson score interval.
            
        Raises:
            ValueError: If *n* ≤ 0 or *x* is outside *[0, n]*, or if *alpha* is not in *(0, 1)*.
        """
        # --- Input validation
        if not (0.0 < alpha < 1.0):
            raise ValueError("alpha must lie strictly between 0 and 1")
        if n <= 0:
            raise ValueError("n must be positive")
        if not (0 <= x <= n):
            raise ValueError("x must satisfy 0 ≤ x ≤ n")

        # --- Wilson score interval
        z = float(norm.ppf(1.0 - alpha / 2.0))
        denom = 1.0 + (z ** 2) / n
        centre = (x + (z ** 2) / 2.0) / n / denom
        half_width = z * np.sqrt((x * (n - x) / n + (z ** 2) / 4.0) / n) / denom
        return centre - half_width, centre + half_width