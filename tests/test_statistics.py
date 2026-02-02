# Test 1: Known difference detection


def test_known_difference():
    arr1 = [0.5] * 100
    arr2 = [0.7] * 100

    from src.statistics import compute_statistics

    results = compute_statistics(arr1, arr2)

    # Check means
    assert results["mean_B"] > results["mean_A"]

    # Check delta close to 0.2
    assert abs(results["delta"] - 0.2) < 1e-9

    # Check confidence interval does not include zero
    assert results["ci_lower"] > 0 or results["ci_upper"] < 0


# Test 2: No difference when models are identical


def test_identical_models():

    # both models have same outcomes
    arr1 = [0.6] * 100
    arr2 = [0.6] * 100

    from src.statistics import compute_statistics

    results = compute_statistics(arr1, arr2)

    # means should be equal
    assert abs(results["mean_A"] - results["mean_B"]) < 1e-9

    # delta should be zero
    assert abs(results["delta"]) < 1e-9

    # confidence interval should include zero
    assert results["ci_lower"] <= 0 <= results["ci_upper"]


# Test 3: Minimum sample size warning


def test_minimum_sample_size_warning():
    arr1 = [0.5]
    arr2 = [0.7]

    from src.statistics import compute_statistics

    results = compute_statistics(arr1, arr2)

    # should return None due to insufficient data
    assert results is None


# Test 4: No effect when distributions are identical

"""def test_no_effect_identical_distributions():
    import numpy as np
    arr1 = [0.5] * 100
    arr2 = [0.5] * 100

    from src.statistics import """
