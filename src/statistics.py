import numpy as np
from scipy import stats
import math

def compute_statistics(outcomes_1, outcomes_2):

    if len(outcomes_1) < 2 or len(outcomes_2) < 2: # ensures enough data for variance calculation
        return None

    mean_A = np.mean(outcomes_1)
    mean_B = np.mean(outcomes_2)

    var_A = np.var(outcomes_1, ddof=1)
    var_B = np.var(outcomes_2, ddof=1)
    n_A = len(outcomes_1)
    n_B = len(outcomes_2)

    # Standard error (Welch)
    se = math.sqrt(var_A / n_A + var_B / n_B)

    # Degrees of freedom (Welch–Satterthwaite)
    df = (var_A / n_A + var_B / n_B) ** 2 / (
        (var_A**2) / (n_A**2 * (n_A - 1)) +
        (var_B**2) / (n_B**2 * (n_B - 1))
    )

    # 95% CI
    t_crit = stats.t.ppf(0.975, df)
    delta = mean_B - mean_A

    lower = delta - t_crit * se
    upper = delta + t_crit * se

    return [mean_A, mean_B, delta, (lower, upper), n_A, n_B]