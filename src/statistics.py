import numpy as np
from scipy import stats
import math

def check_minimum_sample_size(n_A,n_B,min_size):
    """
    Check whether both variants meet the minimum required sample size.

    Parameters:
    n_A : int
        Number of observations for variant A.
    n_B : int
        Number of observations for variant B.
    min_size : int
        Minimum required number of observations per variant.

    Returns:
    bool
        True if both variants meet or exceed the minimum sample size,
        False otherwise.

    Notes:
    - This function encodes a policy decision, not a statistical calculation.
    """
    if (
        n_A < min_size or n_B < min_size
    ):  # ensures enough data for variance calculation
        return False
    else: 
        return True

def calculate_descriptive_statistics(outcomes):
    """
    Compute basic descriptive statistics for a set of outcomes.

    Parameters:
    outcomes : list or array-like
        Numeric outcome values.

    Returns:
    tuple
        (mean, variance, standard deviation, sample size)

    Notes:
    - Uses sample variance and standard deviation (ddof=1).
    - Serves as the single source of truth for descriptive statistics
      used by downstream inference functions.
    """
    mean = np.mean(outcomes)
    var = np.var(outcomes, ddof=1)
    std = np.std(outcomes, ddof=1)
    n = len(outcomes)
    return (mean, var, std, n)

def calculate_welch_test(mean_A, mean_B, var_A, var_B, n_A, n_B):
    """
    
    Compute Welch's t-test components for two variants using precomputed
    descriptive statistics.

    Parameters:
    mean_A, mean_B : float
        Sample means for variants A and B.
    var_A, var_B : float
        Sample variances for variants A and B.
    n_A, n_B : int
        Sample sizes for variants A and B.

    Returns:
    tuple
        (delta, standard_error, degrees_of_freedom)

    Notes:
    - Uses the Welch–Satterthwaite approximation for degrees of freedom.
    - If both variances are zero, returns a zero standard error and
      undefined degrees of freedom (None).
    - This function performs inference only and does not compute
      descriptive statistics.
    """
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
    """
    Compute a two-sided confidence interval for the difference in means.

    Parameters:
    delta : float
        Difference in means (mean_B − mean_A).
    se : float
        Standard error of the difference.
    df : float or None
        Degrees of freedom for the t-distribution.
    confidence_level : float
        Desired confidence level (e.g., 0.95 for a 95% confidence interval).

    Returns:
    tuple
        (lower_bound, upper_bound) of the confidence interval.

    Notes:
    - If standard error is zero, returns a degenerate interval (delta, delta).
    - Assumes a two-sided confidence interval.
    """
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
    Compute statistical evidence comparing two model variants.

    Parameters:
    outcomes_1 : list or array-like
        Numeric outcome values for variant A.
    outcomes_2 : list or array-like
        Numeric outcome values for variant B.

    Returns:
    dict or None
        Dictionary containing raw statistical results:
        - mean_A, mean_B
        - delta (mean_B − mean_A)
        - confidence interval bounds
        - sample sizes
        - effect size (Cohen's d)

        Returns None if minimum sample size requirements are not met.

    Workflow:
    - Validates minimum sample size.
    - Computes descriptive statistics for both variants.
    - Computes Welch inference (delta, standard error, degrees of freedom).
    - Constructs a two-sided 95% confidence interval.
    - Computes effect size (Cohen's d).

    Notes:
    - This function acts as the orchestration layer between descriptive,
      inferential, and interpretive statistics.
    - Returned values are unrounded and intended for downstream consumption.
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