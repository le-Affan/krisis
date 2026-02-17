# Test 4: Assignment stability
from src.models import ModelVariant


def test_assignment_distribution_approximately_balanced(framework):
    # dummy models
    def model_a(x):
        return x + 1

    def model_b(x):
        return x - 1

    framework.register_models(model_a, model_b)

    total_requests = 1000
    probability_split = 0.5

    for _ in range(total_requests):
        framework.route_request(1, probability_split)

    count_a = 0
    count_b = 0

    for req in framework.storage.requests.values():
        if req.selected_model == ModelVariant.A:
            count_a += 1
        elif req.selected_model == ModelVariant.B:
            count_b += 1

    ratio_a = count_a / total_requests

    # Allow randomness, but should be close to 50%
    assert 0.40 <= ratio_a <= 0.60
