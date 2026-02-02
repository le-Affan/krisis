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

def calculate_welch_test(outcomes_1,outcomes_2):
    mean_A = np.mean(outcomes_1)
    mean_B = np.mean(outcomes_2)

    var_A = np.var(outcomes_1, ddof=1)
    var_B = np.var(outcomes_2, ddof=1)

    n_A = len(outcomes_1)
    n_B = len(outcomes_2)

    delta = mean_B - mean_A

    # Standard error (Welch)
    se = math.sqrt(var_A / n_A + var_B / n_B)

    if var_A == 0 and var_B == 0:
        return [mean_A, mean_B, delta, 0.0, None, n_A, n_B]

    # Degrees of freedom (Welch–Satterthwaite)
    df = (var_A / n_A + var_B / n_B) ** 2 / (
        (var_A**2) / (n_A**2 * (n_A - 1)) + (var_B**2) / (n_B**2 * (n_B - 1))
    )

    return [mean_A, mean_B, delta, se, df, n_A, n_B]

def calculate_confidence_interval(delta,se,df,confidence_level):

    if se == 0:
        return (delta, delta)
    
    alpha = 1 -confidence_level
    t_crit = stats.t.ppf(1 - alpha / 2, df)

    lower = delta - t_crit * se
    upper = delta + t_crit * se

    return (lower, upper)

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

    mean_A, mean_B, delta, se, df, n_A, n_B = calculate_welch_test(
        outcomes_1, outcomes_2
        )
    
    ci_lower, ci_upper = calculate_confidence_interval(delta, se, df, 0.95)

    return [mean_A, mean_B, delta, (ci_lower, ci_upper), n_A, n_B]