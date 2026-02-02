# KRISIS — A/B Testing Framework for ML Models

## Overview

KRISIS is a lightweight A/B testing framework designed to compare two machine-learning model variants under real traffic using statistically sound methods.

It curently supports:

* randomized traffic routing
* delayed outcome attribution
* statistical comparison using confidence intervals

The current system is intentionally simple and in-memory, serving as a correct and testable MVP that is being extended with persistence, APIs, and deterministic routing.

---

## Core Concepts

### Model Variants

Two model variants are registered as:

* **Variant A** (baseline)
* **Variant B** (candidate)

---

### Request Routing

Incoming requests are:

* randomly assigned to variant A or B based on a probability split
* logged in memory with a unique `request_id`
* associated with the selected variant for later attribution

---

### Delayed Outcomes

Outcomes are recorded **after** prediction using the `request_id`.

This allows the system to support:

* delayed feedback (e.g. conversions, revenue)
* correct attribution of outcomes to model variants

---

### Statistical Evidence

Once sufficient outcomes are available:

* outcomes are grouped by variant
* Welch’s t-test is used to compare mean outcomes
* a 95% confidence interval for the difference in means is computed

The system emphasizes **uncertainty-aware evidence**, not automated decisions.

---

## Current Project Structure

```
KRISIS/
├── src/
│   ├── core.py           # Routing, state, orchestration
│   └── statistics.py     # Pure statistical computation
├── tests/
│   ├── test_statistics.py
│   ├── test_routing.py
│   └── test_integration.py
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
└── README.md
```

### Design Principles

* **Pure statistics** live in `statistics.py`
* **System wiring** lives in `core.py`
* Tests are split by responsibility:

  * unit tests for statistical correctness
  * routing tests for probabilistic behavior
  * integration tests for end-to-end wiring

---

## How to Run

### 1. Set up environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

### 2. Run tests

```bash
pytest
```

All tests should pass:

* statistical correctness
* routing behavior
* full system integration

---

## Example Usage

```python
from src.core import (
    register_models,
    route_request,
    record_delayed_outcome,
    compile_evidence,
)

# Define two dummy models
def model_a(x):
    return x

def model_b(x):
    return x

# Register models
register_models(model_a, model_b)

# Route requests
request_ids = []
for _ in range(100):
    _, req_id = route_request(1, probability_split=0.5)
    request_ids.append(req_id)

# Record delayed outcomes
for req_id in request_ids:
    record_delayed_outcome(req_id, 1.0)

# Compile statistical evidence
evidence = compile_evidence()
print(evidence)
```

---

## Statistical Methodology

* **Comparison metric:** Difference in mean outcomes (B − A)
* **Test:** Welch’s t-test (unequal variances)
* **Confidence interval:** Two-sided 95%
* **Minimum sample size:** ≥ 2 outcomes per variant

### Edge Case Handling

* Insufficient data → no statistics returned
* Zero variance in both variants → degenerate confidence interval
* Emphasis on confidence intervals over binary significance

---

## Next Planned Extensions

* storage abstraction 
* deterministic routing via hashing
* multi-experiment support
* REST API layer
* database persistence

---

## Why This Exists

Most ML failures happen after deployment, not during training.

KRISIS exists to answer one question rigorously:

> Does this model actually perform better in production ?
