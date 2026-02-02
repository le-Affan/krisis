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


# Test 3: No effect when distributions are identical


def test_no_effect_identical_distributions():

    arr1 = [0.5] * 100
    arr2 = [0.5] * 100

    from src.statistics import compute_statistics

    results = compute_statistics(arr1, arr2)

    # effect size should be zero
    assert abs(results["effect_size"]) < 1e-9


# Test 4: Monte Carlo simulation to validate statistical properties


def test_monte_carlo_confidence_interval_coverage():
    import numpy as np
    from src.statistics import compute_statistics

    n_simulations = 1000
    true_delta = 0.1
    covered = 0

    for _ in range(n_simulations):
        arr1 = np.random.normal(loc=0.5, scale=0.1, size=50).tolist()
        arr2 = np.random.normal(loc=0.6, scale=0.1, size=50).tolist()

        results = compute_statistics(arr1, arr2)

        if results["ci_lower"] <= true_delta <= results["ci_upper"]:
            covered += 1

    coverage_rate = covered / n_simulations

    # 95% CI should cover true value ~95% of the time
    assert 0.9 <= coverage_rate <= 0.99


# Testing all pure functions in statistics.py

# Testing check_minimum_sample_size()


def test_minimum_sample_size_warning():

    from src.statistics import check_minimum_sample_size

    assert check_minimum_sample_size(2, 2, 2) is True
    assert check_minimum_sample_size(1, 2, 2) is False


# Testing calculate_descriptive_statistics()


def test_descriptive_statistics():
    arr = [1, 2, 3, 4, 5]

    from src.statistics import calculate_descriptive_statistics

    mean, var, std, n = calculate_descriptive_statistics(arr)

    assert mean == 3.0
    assert abs(var - 2.5) < 1e-9
    assert abs(std - (2.5**0.5)) < 1e-9
    assert n == 5


# Testing calculate_welch_test()


def test_welch_test():
    mean_A = 1.0
    mean_B = 2.0
    var_A = 1.0
    var_B = 1.5
    n_A = 30
    n_B = 30

    from src.statistics import calculate_welch_test

    delta, se, df = calculate_welch_test(mean_A, mean_B, var_A, var_B, n_A, n_B)

    assert abs(delta - 1.0) < 1e-9
    assert se > 0
    assert df > 0


# Testing edge cases for Welch test where variances are zero


def test_welch_zero_variance():
    from src.statistics import calculate_welch_test

    delta, se, df = calculate_welch_test(1.0, 1.0, 0.0, 0.0, 10, 10)
    assert se == 0
    assert df is None


# Testing calculate_confidence_interval()


def test_confidence_interval():
    delta = 1.0
    se = 0.2
    df = 50
    confidence_level = 0.95

    from src.statistics import calculate_confidence_interval

    ci_lower, ci_upper = calculate_confidence_interval(delta, se, df, confidence_level)

    assert ci_lower < delta < ci_upper


# Testing calculate_effect_size()


def test_effect_size():
    mean_A = 1.0
    mean_B = 2.0
    std_A = 1.0
    std_B = 1.5
    n_A = 30
    n_B = 30

    from src.statistics import calculate_effect_size

    effect_size = calculate_effect_size(mean_A, mean_B, std_A, std_B, n_A, n_B)

    pooled_var = ((n_A - 1) * std_A**2 + (n_B - 1) * std_B**2) / (n_A + n_B - 2)
    pooled_std = pooled_var**0.5

    assert abs(effect_size - ((mean_B - mean_A) / pooled_std)) < 1e-9
