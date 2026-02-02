from src.core import (
    register_models,
    route_request,
    record_delayed_outcome,
    compile_evidence,
)


def test_system_integrates_end_to_end():
    # Dummy models
    def model_a(x):
        return x

    def model_b(x):
        return x

    # 1. Register models
    register_models(model_a, model_b)

    # 2. Route some requests
    request_ids = []
    for _ in range(20):
        _, req_id = route_request(1, probability_split=0.5)
        request_ids.append(req_id)

    # 3. Record outcomes for all requests
    for req_id in request_ids:
        record_delayed_outcome(req_id, 1.0)

    # 4. Compile evidence
    evidence = compile_evidence()

    # ----Integration assertions----

    # System should return a result, not crash
    assert evidence is not None
    assert evidence != "Not enough data to compute statistics."

    # Evidence should have expected structure
    assert isinstance(evidence, dict)

    required_keys = [
        "Model A Mean Outcome",
        "Model B Mean Outcome",
        "Difference in Means (B - A)",
        "95% Confidence Interval",
        "Number of Outcomes for Model A",
        "Number of Outcomes for Model B",
        "Effect Size",
    ]

    for key in required_keys:
        assert key in evidence

    # Counts should be sane
    assert evidence["Number of Outcomes for Model A"] >= 0
    assert evidence["Number of Outcomes for Model B"] >= 0
