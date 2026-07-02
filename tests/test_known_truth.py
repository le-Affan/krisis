"""Known-truth tests: feed the statistical engine data with a known ground
truth and assert it recovers the right answer. These guard against silent
regressions in the inference math."""

import numpy as np

from src.statistics import calculate_effect_size, compute_statistics


def test_recovers_known_large_effect_size():
    # Two groups separated by exactly one standard deviation → Cohen's d ~ 1.0.
    rng = np.random.default_rng(42)
    arr_a = rng.normal(loc=0.0, scale=1.0, size=5000).tolist()
    arr_b = rng.normal(loc=1.0, scale=1.0, size=5000).tolist()

    results = compute_statistics(arr_a, arr_b)

    # Effect size should be close to the known d = 1.0.
    assert abs(results["effect_size"] - 1.0) < 0.1
    # A real one-SD difference must be detected: CI excludes zero.
    assert results["ci_lower"] > 0


def test_detects_no_effect_as_no_effect():
    # Same distribution → true delta is 0; a correct 95% CI should include it.
    rng = np.random.default_rng(7)
    arr_a = rng.normal(loc=0.5, scale=0.1, size=2000).tolist()
    arr_b = rng.normal(loc=0.5, scale=0.1, size=2000).tolist()

    results = compute_statistics(arr_a, arr_b)

    assert results["ci_lower"] <= 0 <= results["ci_upper"]
    assert abs(results["effect_size"]) < 0.1


def test_effect_size_sign_matches_direction():
    # B worse than A → negative effect size.
    d = calculate_effect_size(
        mean_A=1.0, mean_B=0.0, std_A=1.0, std_B=1.0, n_A=100, n_B=100
    )
    assert d < 0
