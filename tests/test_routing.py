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

    request_ids = []

    for _ in range(total_requests):
        _, request_id = framework.route_request(1, probability_split)
        request_ids.append(request_id)

    count_a = 0
    count_b = 0

    for req_id in request_ids:
        req = framework.storage.get_request(req_id)
        if req.selected_model == ModelVariant.A:
            count_a += 1
        elif req.selected_model == ModelVariant.B:
            count_b += 1

    ratio_a = count_a / total_requests

    # Allow randomness, but should be close to 50%
    assert 0.40 <= ratio_a <= 0.60
