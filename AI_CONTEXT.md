# Project Context: ML Model A/B Testing Framework

## Project Purpose

This system is a backend experimentation framework that compares two ML models under real traffic and provides statistical evidence about which performs better.

The system routes prediction requests between model variants, records predictions, ingests delayed outcomes, and computes statistical comparisons such as difference in means and confidence intervals.

The system reports evidence but does not automatically choose a winner.

## Core System Flow

1. User registers two models.
2. User creates an experiment with a traffic split.
3. Client sends prediction requests to the framework.
4. Router assigns request to model A or B.
5. Prediction is logged with request_id.
6. Later the client reports an outcome for that request.
7. Statistical engine computes comparison results.

## Backend Technology

Language: Python
Framework: FastAPI
Database: PostgreSQL
Statistics: NumPy, SciPy

## Important Backend Endpoints

Health check

GET /health

Prediction routing

POST /api/v1/predict

Report outcome

POST /api/v1/outcomes

Get experiment results

GET /api/v1/experiments/{experiment_id}/results

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
