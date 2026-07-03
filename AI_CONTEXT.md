# Project Context: ML Model A/B Testing Framework

## Project Purpose

This system is a backend experimentation framework that compares two ML models under real traffic and provides statistical evidence about which performs better.

The system routes prediction requests between model variants, records predictions, ingests delayed outcomes, and computes statistical comparisons such as difference in means and confidence intervals.

The system reports evidence but does not automatically choose a winner.

## Core System Flow

1. User registers two real models via `POST /api/v1/models`.
2. User creates an experiment referencing those model IDs (`model_a_id`,
   `model_b_id`); creation is rejected with 400 if either isn't registered.
3. Client sends prediction requests to the framework.
4. Router assigns request to model A or B using the experiment's split, then
   resolves that variant's model_id through the registry and invokes it via
   its adapter (`http` or `python_callable`).
5. Prediction is logged with request_id.
6. Later the client reports an outcome for that request.
7. Statistical engine computes comparison results.

## Model Registry — Working, Two Adapter Types Only

`POST /api/v1/models` is implemented (`src/api/routes/models.py`) and wired
into routing (`ABTestFramework._invoke_variant` in `src/core.py`). There are
no hardcoded model stand-ins.

* `adapter_type: "http"` — `location` is a URL. Krisis POSTs `features` as
  JSON and expects `{"prediction": ...}` back. Safe for untrusted-reachable
  deployments.
* `adapter_type: "python_callable"` — `location` is
  `"module.path:function_name"`, imported and called in-process.
  **Executes arbitrary local code — local/single-user use only, never on a
  deployment reachable by untrusted users.**

A model exception during prediction returns HTTP 502 for that request; it
does not crash the service.

## Backend Technology

Language: Python
Framework: FastAPI
Database: SQLite (dev default, zero-config) or PostgreSQL (prod), via SQLAlchemy + Alembic
Statistics: NumPy, SciPy

## Backend Endpoints

Full current list — see README.md "API reference" for descriptions:

GET /health
GET /metrics
GET /metrics/app
POST /api/v1/models
GET /api/v1/models
GET /api/v1/models/{model_id}
POST /api/v1/experiments
GET /api/v1/experiments
GET /api/v1/experiments/{experiment_id}
PATCH /api/v1/experiments/{experiment_id}
POST /api/v1/predict
POST /api/v1/outcomes
GET /api/v1/experiments/{experiment_id}/results
POST /api/v1/sample-size-calculator
GET /api/v1/experiments/{experiment_id}/timeseries

## Expected Prediction Request

{
"experiment_id": "example_exp",
"features": {...}
}

## Expected Outcome Request

{
"request_id": "req_123",
"value": 1
}

## Statistical Output

The system computes:

* mean outcome for variant A
* mean outcome for variant B
* difference in means
* confidence interval
* sample size per variant

## Goal of the UI

The UI must only call existing API endpoints.

The UI must not modify backend logic.

The UI must provide four pages:

Experiments page

* create experiment
* list experiments

Predictions page

* send prediction request
* display assigned variant

Outcomes page

* report outcome using request_id

Results dashboard

* show statistical comparison between models
* charts for means, effect size, confidence interval

## Strict Rules

The AI must not invent backend functionality.

The AI must only use the provided endpoints.

The AI must produce a deterministic implementation.

The UI must be a Next.js dashboard using React and charts.

The UI will be deployed separately from the FastAPI backend.
