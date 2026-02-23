<div align="center">

# ⚔️ KRISIS

### Production-Grade A/B Experimentation Framework for Machine Learning Systems

**Online Evidence. Statistical Rigor. Zero Guesswork.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-API%20Layer-009688.svg)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Storage-336791.svg)]()
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

</div>

---

## What Is KRISIS?

KRISIS is a **production-shaped A/B testing framework for machine learning models**.

It routes live traffic between competing model variants, captures delayed real-world outcomes, and computes statistically rigorous evidence, enabling teams to answer one critical question:

> Does this model actually perform better in production?

Most ML evaluation happens offline.
KRISIS exists to bring **online experimental evidence** into the loop.

---

## Why This Exists

Offline metrics lie.

* Distribution shift
* Proxy targets
* Noisy labels
* Delayed outcomes
* Tiny effect sizes

Accuracy improvements in notebooks often disappear in production.

KRISIS closes the gap between:

**Offline evaluation → Live traffic → Statistical certainty**

---

## Architecture Overview

```
Client Request
      ↓
FastAPI Layer
      ↓
Traffic Router
      ↓
Model Variant
      ↓
Prediction Logger
      ↓
Delayed Outcome Ingestion
      ↓
Statistical Engine
      ↓
Evidence & Confidence Intervals
```

The system separates:

* **Routing logic**
* **Storage abstraction**
* **Statistical computation**
* **API layer orchestration**

This ensures clean boundaries and extensibility.

---

## Core Capabilities

### Randomized Traffic Routing

* Probabilistic split between model A and B
* Unique request tracking
* Variant attribution for every prediction

### Delayed Outcome Attribution

* Outcomes recorded asynchronously
* Correct linking via unique `request_id`
* Supports real-world feedback in the form of conversion, revenue, etc.

### Statistical Engine

* Welch’s t-test (unequal variance)
* Difference in means (B − A)
* 95% confidence intervals
* Effect size reporting
* Minimum sample guardrails

KRISIS does not auto-deploy winners.
It provides evidence for humans to decide.

---

## Current Project Structure

```
KRISIS/
├── src/
│   ├── core.py              # Routing, orchestration, storage wiring
│   ├── statistics.py        # Pure statistical computation
│   ├── api/                 # FastAPI layer
│   ├── storage/             # In-memory / database backends
│   └── models/              # Data models
├── tests/
│   ├── test_statistics.py
│   ├── test_routing.py
│   └── test_integration.py
├── requirements.txt
└── README.md
```

### Design Principles

* Pure statistical logic isolated from system wiring
* Storage abstraction (memory → database)
* Deterministic extension-ready routing
* API-first architecture
* Test-driven validation

---

## Statistical Methodology

**Metric:** Difference in mean outcomes (B − A)

**Test:** Welch’s t-test (unequal variances)

**Confidence Interval:** Two-sided 95%

**Guardrails:** Minimum outcomes per variant

Edge cases handled:

* Insufficient data
* Degenerate variance
* High variance warnings

KRISIS emphasizes uncertainty-aware evidence over binary "significance".

---

## API Layer (In Progress)

FastAPI-based REST interface:

* `POST /predict` → Route traffic and return prediction
* `POST /outcomes` → Record delayed outcomes
* `GET /results` → Retrieve statistical evidence
* `GET /health` → System health check

Interactive docs available at:

```
/api/v1/docs
```

---

## Quickstart

### 1️⃣ Setup Environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2️⃣ Run Tests

```bash
pytest
```

All tests validate:

* Routing behavior
* Statistical correctness
* End-to-end system integrity

---

## Example Usage

```python
from src.core import ABTestFramework

framework = ABTestFramework()

# Register models
framework.register_models(model_a, model_b)

# Route traffic
prediction, request_id = framework.route_request(
    X=data,
    probability_split=0.5
)

# Record delayed outcome
framework.record_delayed_outcome(request_id, outcome=1.0)

# Compile evidence
results = framework.compile_evidence()
print(results)
```

---

## Roadmap

✔ Core routing engine
✔ Statistical computation module
✔ Storage abstraction
✔ FastAPI layer
🔄 Database persistence
⬜ Deterministic routing via hashing
⬜ Multi-experiment support
⬜ Public deployment

---

## Deployment Vision

KRISIS is designed to evolve into:

* Horizontally scalable API service
* PostgreSQL-backed experimentation system
* Containerized production deployment
* Experiment lifecycle management
* Evidence reporting with stability signals

This is infrastructure — not a notebook experiment.

---

## The Philosophy

Machine learning systems fail silently in production.

KRISIS introduces a missing discipline:

**Treat model deployment like a scientific experiment.**

Randomization.
Attribution.
Statistical uncertainty.
Evidence over intuition.

---

## 📜 License

MIT License

---

<div align="center">

### KRISIS

**Because shipping models without evidence is gambling.**

</div>
