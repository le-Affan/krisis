<div align="center">

# ⚔️ KRISIS

### A/B Testing Framework for Machine Learning Systems

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
* Supports real-world feedback such as conversions, revenue, engagement etc.

### Statistical Engine

* Welch’s t-test (unequal variance)
* Difference in means (B − A)
* 95% confidence intervals
* Effect size reporting
* Minimum sample guardrails

KRISIS does **not auto-deploy winners**.
It provides evidence so humans can make the final decision.

---

## Current Project Structure

```
KRISIS/
├── src/
│   ├── core.py              # ABTestFramework: routing + orchestration
│   ├── statistics.py        # Statistical computation engine (Welch, CI, effect size)
│   ├── storage.py           # StorageBackend ABC + InMemory & Database backends
│   ├── models.py            # Dataclass domain models (Model, Request, Outcome, ...)
│   ├── db_models.py         # SQLAlchemy ORM tables
│   ├── database.py          # Engine / session factory
│   ├── config.py            # Pydantic settings
│   └── api/                 # FastAPI layer (main.py + routes/ + schemas/)
├── migrations/              # Alembic migrations
├── tests/
│   ├── test_statistics.py
│   ├── test_known_truth.py
│   ├── test_routing.py
│   ├── test_db.py
│   ├── test_api.py
│   ├── test_config.py
│   └── test_integration.py
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Dev/test tooling (includes -r requirements.txt)
└── README.md
```

### Model Registry

Register a model before referencing it in an experiment:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/models \
-H "Content-Type: application/json" \
-d '{
  "model_id": "baseline_model",
  "adapter_type": "python_callable",
  "location": "my_package.models:predict_baseline"
}'
```

Two adapter types are supported — nothing else:

* **`http`** — `location` is a URL. Krisis POSTs the input `features` as
  JSON to it and expects back JSON containing a `"prediction"` field, e.g.
  `{"prediction": 0.73}`. 5s timeout. Safe for any deployment, including
  ones reachable by untrusted users.
* **`python_callable`** — `location` is `"module.path:function_name"`,
  importable in the **same Python environment running Krisis**. The
  function is called directly with the features dict.
  **Security: this executes local code with no sandboxing. Only use it for
  local/single-user development. Never register a `python_callable` model
  on a Krisis deployment reachable by untrusted users** — see
  `DEPLOYMENT.md` → Security Considerations.

`python_callable` is validated at registration time (the import is
resolved immediately, so a bad module/function path fails with a 400
instead of surfacing later at prediction time). `POST /api/v1/experiments`
requires both `model_a_id` and `model_b_id` to already be registered — it
returns 400 otherwise. There are no hardcoded model stand-ins; every
prediction is routed to a real registered model.

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

KRISIS emphasizes **uncertainty-aware evidence** rather than binary "significance" decisions.

---

# Running the System

## 1. Setup Environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt   # runtime + test tooling
```

---

## 2. Start the API Server

```bash
uvicorn src.api.main:app --reload
```

No environment variables required. With defaults, KRISIS uses a local SQLite
database (`abtest.db`) and runs Alembic migrations automatically on startup.
Server runs at:

```
http://127.0.0.1:8000
```

Interactive API docs:

```
http://127.0.0.1:8000/docs
```

---

# Example API Usage

## Create Experiment

```bash
curl -X POST http://127.0.0.1:8000/api/v1/experiments \
-H "Content-Type: application/json" \
-d '{
  "experiment_id": "rec_model_test",
  "model_a_id": "baseline_model",
  "model_b_id": "candidate_model",
  "probability_split": 0.5,
  "metric_type": "continuous",
  "confidence_level": 0.95
}'
```

---

## Send Prediction

```bash
curl -X POST http://127.0.0.1:8000/api/v1/predict \
-H "Content-Type: application/json" \
-d '{
  "experiment_id": "rec_model_test",
  "features": {"x": 10}
}'
```

Example response

```json
{
  "request_id": "abc123",
  "prediction": 0.73,
  "model_variant": "A",
  "timestamp": "2026-03-05T12:30:00Z"
}
```

---

## Report Outcome

```bash
curl -X POST http://127.0.0.1:8000/api/v1/outcomes \
-H "Content-Type: application/json" \
-d '{
  "request_id": "REQUEST_ID_HERE",
  "value": 1
}'
```

---

## Get Experiment Results

```bash
curl http://127.0.0.1:8000/api/v1/experiments/rec_model_test/results
```

---

## System Monitoring

Prometheus scrape endpoint:

```
GET /metrics
```

Application metrics (JSON: experiment/request/outcome counts, uptime):

```
GET /metrics/app
```

Health check:

```
GET /health
```

---

# Running Tests

```bash
pytest
```

Tests validate:

* Routing behavior
* Statistical correctness
* End-to-end system integrity

---

# Deployment Vision

KRISIS is designed to evolve into:

* Horizontally scalable API service
* PostgreSQL-backed experimentation infrastructure
* Containerized production deployment
* Experiment lifecycle management
* Evidence reporting with stability signals

This project is intended to represent **real experimentation infrastructure**, not a notebook prototype.

---

# Philosophy

Machine learning systems fail silently in production.

KRISIS introduces a missing discipline:

**Treat model deployment like a scientific experiment.**

Randomization.
Attribution.
Statistical uncertainty.
Evidence over intuition.

---

<div align="center">

### KRISIS

**Because shipping models without evidence is gambling.**

</div>
