# Test 1: Known difference detection

def test_known_difference():
    arr1 = [0.5] * 100
    arr2 = [0.7] * 100

    from src.statistics import compute_statistics
    results = compute_statistics(arr1, arr2)

    mean_A, mean_B, delta, (lower, upper), n_A, n_B = results

    # Check means
    assert mean_B > mean_A

    # Check delta close to 0.2
    assert abs(delta - 0.2) < 1e-9

    # Check confidence interval does not include zero
    assert lower > 0 or upper < 0


# Test 2: No difference when models are identical

def test_identical_models():

    # both models have same outcomes
    arr1 = [0.6] * 100
    arr2 = [0.6] * 100

    from src.statistics import compute_statistics
    results = compute_statistics(arr1, arr2)

    mean_A, mean_B, delta, (lower, upper), n_A, n_B = results

    # means should be equal
    assert abs(mean_A - mean_B) < 1e-9

    # delta should be zero
    assert abs(delta) < 1e-9

    # confidence interval should include zero
    assert lower <= 0 <= upper
