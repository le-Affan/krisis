import numpy as np
from scipy import stats
import math

def check_minimum_sample_size(n_A,n_B,min_size):
    if (
        n_A < min_size or n_B < min_size
    ):  # ensures enough data for variance calculation
        return False
    else: 
        return True

def calculate_descriptive_statistics(outcomes):
    mean = np.mean(outcomes)
    var = np.var(outcomes, ddof=1)
    std = np.std(outcomes, ddof=1)
    n = len(outcomes)
    return (mean, var, std, n)

def calculate_welch_test(mean_A, mean_B, var_A, var_B, n_A, n_B):
    delta = mean_B - mean_A

    # Standard error (Welch)
    se = math.sqrt(var_A / n_A + var_B / n_B)

    if var_A == 0 and var_B == 0:
        return (delta, 0.0, None)

    # Degrees of freedom (Welch–Satterthwaite)
    df = (var_A / n_A + var_B / n_B) ** 2 / (
        (var_A**2) / (n_A**2 * (n_A - 1)) + (var_B**2) / (n_B**2 * (n_B - 1))
    )

    return (delta, se, df)

def calculate_confidence_interval(delta,se,df,confidence_level):

    if se == 0:
        return (delta, delta)
    
    alpha = 1 -confidence_level
    t_crit = stats.t.ppf(1 - alpha / 2, df)

    lower = delta - t_crit * se
    upper = delta + t_crit * se

    return (lower, upper)

def calculate_effect_size(mean_A, mean_B, std_A, std_B, n_A, n_B):
    """
    Compute Cohen's d to measure effect size between two groups.

    Parameters:
    mean_A, mean_B : float
        Sample means for variants A and B.
    std_A, std_B : float
        Sample standard deviations for variants A and B.
    n_A, n_B : int
        Sample sizes for variants A and B.

    Returns:
    float
        Cohen's d effect size. Returns 0.0 if pooled standard deviation is zero.
    """
    # Pooled standard deviation
    pooled_var = (
        ((n_A - 1) * std_A**2 + (n_B - 1) * std_B**2) / (n_A + n_B - 2)
    )

    if pooled_var == 0:
        return 0.0

    pooled_std = math.sqrt(pooled_var)

    return (mean_B - mean_A) / pooled_std


def compute_statistics(outcomes_1, outcomes_2):
    """
    Compute a statistical comparison between two model variants using Welch's t-test.

    Parameters:
    outcomes_1 : list or array-like
        Numeric outcome values for variant A.
    outcomes_2 : list or array-like
        Numeric outcome values for variant B.

    Returns:
    list or None
        [mean_A, mean_B, delta, (CI_lower, CI_upper), n_A, n_B] if sufficient data
        is available, otherwise None.

    Statistical Method:
    - Computes sample means and variances for each variant.
    - Uses Welch–Satterthwaite approximation to estimate degrees of freedom.
    - Constructs a two-sided 95% confidence interval for the difference in means
      (mean_B − mean_A).

    Edge Cases:
    - Returns None if either variant has fewer than two observations.
    - If both variants have zero variance, returns a degenerate confidence interval
      where CI_lower == CI_upper == delta.

    Assumptions:
    - Outcomes are continuous and approximately normally distributed.
    - Samples are independent between variants.
    """
    if not check_minimum_sample_size(len(outcomes_1), len(outcomes_2), 2):
        return None

    mean_A,var_A,std_A,n_A = calculate_descriptive_statistics(outcomes_1)
    mean_B,var_B,std_B,n_B = calculate_descriptive_statistics(outcomes_2)

    delta, se, df = calculate_welch_test(mean_A, mean_B, var_A, var_B, n_A, n_B)

    ci_lower, ci_upper = calculate_confidence_interval(delta, se, df, 0.95)

    effect_size = calculate_effect_size(mean_A, mean_B, std_A, std_B, n_A, n_B)

    return {
        "mean_A": mean_A, 
        "mean_B": mean_B, 
        "delta": delta, 
        "ci_lower": ci_lower, 
        "ci_upper": ci_upper, 
        "n_A": n_A, 
        "n_B": n_B, 
        "effect_size": effect_size
        }