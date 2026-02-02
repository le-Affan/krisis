import numpy as np
from scipy import stats
import math

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
    if len(outcomes_1) < 2 or len(outcomes_2) < 2: # ensures enough data for variance calculation
        return None

    mean_A = np.mean(outcomes_1)
    mean_B = np.mean(outcomes_2)

    var_A = np.var(outcomes_1, ddof=1)
    var_B = np.var(outcomes_2, ddof=1)

    n_A = len(outcomes_1)
    n_B = len(outcomes_2)

    delta = mean_B - mean_A


    # Both groups have zero variance; return delta as 0 and CI as (0,0)
    if var_A == 0 and var_B == 0:
        return [mean_A, mean_B, delta, (0.0, 0.0), n_A, n_B] 


    # Standard error (Welch)
    se = math.sqrt(var_A / n_A + var_B / n_B)


    # Degrees of freedom (Welch–Satterthwaite)
    df = (var_A / n_A + var_B / n_B) ** 2 / (
        (var_A**2) / (n_A**2 * (n_A - 1)) +
        (var_B**2) / (n_B**2 * (n_B - 1))
    )
      

    # 95% CI
    t_crit = stats.t.ppf(0.975, df)

    lower = delta - t_crit * se
    upper = delta + t_crit * se

    return [mean_A, mean_B, delta, (lower, upper), n_A, n_B]