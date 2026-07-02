"""Timeseries endpoint test: inject predictions+outcomes spread over time and
confirm cumulative sample sizes are non-decreasing and CIs generally narrow."""

import numpy as np
from fastapi.testclient import TestClient

from src.api.main import app, get_framework
from src.core import ABTestFramework
from src.models import ModelVariant, Outcome, Request
from src.storage import InMemoryStorage


def _build_framework():
    framework = ABTestFramework(storage_backend=InMemoryStorage())
    framework.register_models(lambda x: x, lambda x: x)
    return framework


def test_timeseries_converges():
    framework = _build_framework()
    app.dependency_overrides[get_framework] = lambda: framework

    rng = np.random.default_rng(1)
    base = 1_700_000_000.0  # fixed epoch
    exp = "ts_exp"

    # 300 events spread 60s apart -> ~5h span. A ~ N(0.5,0.1), B ~ N(0.7,0.1).
    for i in range(300):
        ts = base + i * 60
        variant = ModelVariant.A if i % 2 == 0 else ModelVariant.B
        mean = 0.5 if variant == ModelVariant.A else 0.7
        rid = f"req_{i}"
        framework.storage.save_request(
            Request(
                request_id=rid,
                selected_model=variant,
                input_data=None,
                timestamp=ts,
                experiment_id=exp,
            )
        )
        framework.storage.save_outcome(
            Outcome(
                request_id=rid,
                outcome_value=float(rng.normal(mean, 0.1)),
                timestamp=ts,
            )
        )

    client = TestClient(app)
    resp = client.get(f"/api/v1/experiments/{exp}/timeseries?window=1h")
    assert resp.status_code == 200
    buckets = resp.json()["buckets"]

    # Multiple buckets returned.
    assert len(buckets) >= 3

    # Cumulative sample sizes never decrease.
    sizes_a = [b["sample_size_a"] for b in buckets]
    sizes_b = [b["sample_size_b"] for b in buckets]
    assert sizes_a == sorted(sizes_a)
    assert sizes_b == sorted(sizes_b)

    # CI generally narrows: width at the last bucket < width at the first
    # bucket that has a CI.
    widths = [
        b["ci_upper"] - b["ci_lower"]
        for b in buckets
        if b["ci_lower"] is not None and b["ci_upper"] is not None
    ]
    assert len(widths) >= 2
    assert widths[-1] < widths[0]

    app.dependency_overrides.clear()
