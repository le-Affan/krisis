"""Sample-size calculator tests.

Reference value derived independently (not via the function under test):
  p1 = 0.10, p2 = 0.12
  z_{1-alpha/2} = 1.959964 (alpha=0.05), z_{power} = 0.841621 (power=0.8)
  n = (1.959964 + 0.841621)^2 * (0.1*0.9 + 0.12*0.88) / (0.02^2)
    = 7.848882 * 0.1956 / 0.0004
    = 3838.10...  -> ceil -> 3839
"""

from fastapi.testclient import TestClient

from src.api.main import app
from src.statistics import required_sample_size_two_proportions

client = TestClient(app)

REFERENCE_N = 3839


def test_matches_hand_calculated_reference():
    n = required_sample_size_two_proportions(
        baseline_rate=0.1, minimum_detectable_effect=0.02, power=0.8, alpha=0.05
    )
    assert n == REFERENCE_N


def test_endpoint_returns_reference():
    resp = client.post(
        "/api/v1/sample-size-calculator",
        json={"baseline_rate": 0.1, "minimum_detectable_effect": 0.02},
    )
    assert resp.status_code == 200
    assert resp.json()["required_sample_size_per_variant"] == REFERENCE_N


def test_endpoint_rejects_rate_plus_effect_over_one():
    resp = client.post(
        "/api/v1/sample-size-calculator",
        json={"baseline_rate": 0.95, "minimum_detectable_effect": 0.1},
    )
    assert resp.status_code == 400
