from fastapi.testclient import TestClient

from src.api.main import app, get_framework
from src.core import ABTestFramework

client = TestClient(app)


def create_test_framework():
    framework = ABTestFramework()

    def model_a(x):
        return 1.0

    def model_b(x):
        return 2.0

    framework.register_models(model_a, model_b)
    return framework


def override_framework(framework):
    app.dependency_overrides[get_framework] = lambda: framework


def clear_override():
    app.dependency_overrides.clear()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_predict_endpoint():
    framework = create_test_framework()
    override_framework(framework)

    response = client.post(
        "/api/v1/predict",
        json={"experiment_id": "test_exp", "features": {"x": 1.0}},
    )

    assert response.status_code == 200
    assert "request_id" in response.json()

    clear_override()


def test_outcome_endpoint():
    framework = create_test_framework()
    override_framework(framework)

    # First make a prediction
    pred_response = client.post(
        "/api/v1/predict",
        json={"experiment_id": "test_exp", "features": {"x": 1.0}},
    )
    request_id = pred_response.json()["request_id"]

    # Then report outcome
    outcome_response = client.post(
        "/api/v1/outcomes",
        json={"request_id": request_id, "value": 0.75},
    )

    assert outcome_response.status_code == 200

    clear_override()


def test_results_endpoint():
    framework = create_test_framework()
    override_framework(framework)

    # Generate multiple predictions and outcomes
    for _ in range(3):
        pred_response = client.post(
            "/api/v1/predict",
            json={"experiment_id": "test_exp", "features": {"x": 1.0}},
        )
        request_id = pred_response.json()["request_id"]

        client.post(
            "/api/v1/outcomes",
            json={"request_id": request_id, "value": 0.75},
        )

    response = client.get("/api/v1/experiments/test_exp/results")

    # Depending on minimum sample logic
    assert response.status_code in [200, 400]

    clear_override()
