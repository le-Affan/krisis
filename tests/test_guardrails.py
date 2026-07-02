"""Guardrail warning tests: one per warning type (data guaranteed to trigger
it) plus one confirming clean data produces zero warnings."""

import numpy as np

from src.statistics import compute_guardrail_warnings


def test_insufficient_sample_size_warns():
    # n < 100 per variant, balanced assignment, no variance -> only the
    # sample-size warning should fire.
    warnings = compute_guardrail_warnings(
        [0.5] * 50, [0.5] * 50, configured_split=0.5, count_A=50, count_B=50
    )
    assert any("Sample size below recommended minimum" in w for w in warnings)
    assert not any("Assignment imbalance" in w for w in warnings)


def test_assignment_imbalance_warns():
    # Enough outcomes (no sample-size warning) but 90/10 assignment vs a
    # configured 50/50 split -> imbalance warning.
    warnings = compute_guardrail_warnings(
        [0.5] * 150, [0.5] * 150, configured_split=0.5, count_A=900, count_B=100
    )
    assert any("Assignment imbalance" in w for w in warnings)
    assert not any("Sample size below recommended minimum" in w for w in warnings)


def test_high_variance_warns():
    # Large spread, ~zero true effect -> pooled std dwarfs the difference.
    rng = np.random.default_rng(0)
    a = rng.normal(0.5, 1.0, size=200).tolist()
    b = rng.normal(0.5, 1.0, size=200).tolist()
    warnings = compute_guardrail_warnings(
        a, b, configured_split=0.5, count_A=200, count_B=200
    )
    assert any("High variance relative to effect size" in w for w in warnings)


def test_clean_data_no_warnings():
    # >=100 per variant, balanced, tight distributions, clear effect.
    warnings = compute_guardrail_warnings(
        [0.5] * 150, [0.7] * 150, configured_split=0.5, count_A=150, count_B=150
    )
    assert warnings == []
