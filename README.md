<div align="center">

# ⚔️ KRISIS

### Online A/B testing for ML models

[![Python](https://img.shields.io/badge/Python-3.11%2F3.12-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-API%20Layer-009688.svg)]()
[![Tests](https://img.shields.io/badge/tests-74%20passing-brightgreen.svg)]()
[![Docker](https://img.shields.io/badge/Docker-verified-2496ED.svg)]()
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

</div>

---

## What is Krisis?

Offline model evaluation lies to you sometimes. A model can look to be better on a test set offline but once it's serving real traffic, because the offline number doesn't account for sampling noise, distribution shift, or how small the actual gap was to begin with.

Krisis is a small, self-hosted service that routes live prediction traffic between two model variants, records what each one predicted, collects the real-world outcome for each prediction (often arriving later than the prediction itself), and runs the actual statistics — a Welch's t-test, a 95% confidence interval, an effect size — to tell you whether one model is *really* better, or whether you're looking at noise. It doesn't auto-promote a winner. It gives you the evidence and gets out of the way.

## Proof it works

Two independently trained spam classifiers were registered with Krisis and put through a real 50/50 traffic split against the [SMS Spam Collection](https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip) test set — 1008 live `/predict` + `/outcomes` calls over real HTTP against a running Krisis instance. Full walkthrough with raw request/response output: [`results/DEMO_REPORT.md`](results/DEMO_REPORT.md).

Offline, Model B (TF-IDF + Logistic Regression) looked marginally *worse* than Model A (keyword-count Naive Bayes) — 98.03% vs 98.30% accuracy on the held-out test set. The online experiment measured it directly:

| | |
|---|---|
| sample size (A / B) | 512 / 496 |
| accuracy (A / B) | 0.9844 / 0.9778 |
| 95% CI on the difference | **[−0.0234, 0.0103]** — includes zero |
| guardrail warning | *"High variance relative to effect size... confidence interval will be wide and unreliable"* |
| `/predict` latency | p50 6.74ms · p95 7.75ms · p99 9.06ms |

The CI includes zero and Krisis's own guardrail flags the result as unreliable at this sample size — correctly refusing to call a 0.66pp gap "significant." That's the whole point: catching the difference between a real effect and noise before someone ships a decision on it.

## Quickstart

Two verified paths. Pick one.

### Bare uvicorn (SQLite, zero config)

```bash
python -m venv venv && source venv/bin/activate   # Python 3.11 or 3.12
pip install -r requirements-dev.txt
uvicorn src.api.main:app --reload
```

No environment variables needed. Migrations run automatically on startup against a local `abtest.db`. Server: `http://127.0.0.1:8000` — interactive docs at `/docs`.

### Docker Compose (Postgres + API)

```bash
docker compose up -d --build
curl http://localhost:8000/health
```

> **SELinux hosts (Fedora etc.):** if you edit `docker-compose.yml`'s bind mounts, keep the `:z` label on `./src` and `./backups` — without it the container silently can't read the mounted files.

Both paths are verified end-to-end (migration runs, health check passes, a full experiment → predict → outcome → results round trip works). The `docker-compose.prod.yml` / nginx / monitoring stack and `scripts/startup.sh` exist and are documented in `DEPLOYMENT.md`, but have **not** been run end-to-end in this repo's own verification passes — treat as unverified until you've run it yourself.

## Core concepts

- **Experiment** — a comparison between two registered models (`model_a_id`, `model_b_id`) with a configured traffic split.
- **Variant** — "A" or "B". Each incoming prediction request is randomly assigned one, per the experiment's `probability_split`.
- **Delayed outcome** — the real-world result of a prediction (did the user convert, was the classification correct, etc.) often isn't known until later. `POST /api/v1/outcomes` links it back to the original prediction via `request_id`.
- **Guardrail warnings** — `GET .../results` doesn't just report numbers; it flags when the sample size is too small, when traffic assignment has drifted from the configured split, or when variance is too high relative to the observed effect for the CI to mean much.
- **Confidence interval** — a 95% CI on the difference in means (B − A), via Welch's t-test (no equal-variance assumption). If it includes zero, the difference isn't distinguishable from noise at this sample size.

## API reference

All endpoints below exist in the code today — verified against `src/api/routes/*.py`, not aspirational.

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus scrape endpoint |
| GET | `/metrics/app` | App metrics (JSON: counts + uptime) |
| POST | `/api/v1/models` | Register a model (`http` or `python_callable` adapter) |
| GET | `/api/v1/models` | List registered models |
| GET | `/api/v1/models/{model_id}` | Get one registered model |
| POST | `/api/v1/experiments` | Create an experiment (400 if either model isn't registered) |
| GET | `/api/v1/experiments` | List experiments |
| GET | `/api/v1/experiments/{experiment_id}` | Get one experiment |
| PATCH | `/api/v1/experiments/{experiment_id}` | Update experiment status |
| POST | `/api/v1/predict` | Route a prediction to a variant, log it |
| POST | `/api/v1/outcomes` | Report the real-world outcome for a prediction |
| GET | `/api/v1/experiments/{experiment_id}/results` | Statistical results + guardrail warnings |
| POST | `/api/v1/sample-size-calculator` | Required sample size for a target effect (power analysis) |
| GET | `/api/v1/experiments/{experiment_id}/timeseries` | Cumulative stats bucketed over time (watch the CI converge) |

## Bring your own models

Register a model before referencing it in an experiment:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/models \
  -H "Content-Type: application/json" \
  -d '{"model_id": "baseline", "adapter_type": "python_callable", "location": "my_package.models:predict_fn"}'
```

Exactly two adapter types, nothing else:

- **`http`** — `location` is a URL. Krisis POSTs `{"...features"}` as JSON and expects back `{"prediction": ...}`. 5s timeout, clear errors on unreachable/malformed/non-200 responses. Safe for any deployment, including ones reachable by untrusted users.
- **`python_callable`** — `location` is `"module.path:function_name"`, imported and called in-process. **This executes arbitrary local code with no sandboxing — local/single-user development only. Never register a `python_callable` model on a deployment reachable by untrusted users.** See `DEPLOYMENT.md` → Security Considerations for the full reasoning.

`python_callable` imports are resolved immediately at registration time, so a typo'd module path fails with a 400 there, not later at prediction time. A working example: [`demo/spam_models.py`](demo/spam_models.py), which wraps two real trained scikit-learn models this way.

## Reproduce the demo yourself

```bash
pip install -r requirements-demo.txt        # adds scikit-learn, pandas, joblib
python scripts/train_models.py              # downloads SMS Spam Collection, trains both models, prints real accuracy
uvicorn src.api.main:app --reload &          # boot Krisis (separate terminal is cleaner)
# register demo.spam_models:predict_model_a / predict_model_b via POST /api/v1/models,
# create an experiment referencing them — see results/DEMO_REPORT.md for the exact calls
python scripts/simulate_traffic.py --n 1000  # replays held-out test examples through /predict + /outcomes
python scripts/build_report.py               # pulls /results + /timeseries, computes latency percentiles, saves to results/
```

## Known limitations

- **No authentication on any endpoint.** Anyone who can reach the API can register models, including `python_callable` ones. Don't expose Krisis to untrusted networks without putting authentication in front of it yourself.
- **`docker-compose.prod.yml` (nginx + monitoring stack) and `scripts/startup.sh` are unverified.** The base `docker-compose.yml` (Postgres + API) and both Dockerfiles are verified working end-to-end; the full production compose stack with nginx/Prometheus/Grafana has not been.
- **No rate limiting, no multi-tenancy, no experiment-lifecycle automation** (e.g. auto-stopping an experiment once significance is reached) — reporting evidence is the whole scope; decisions are yours.

## Tech stack & architecture

Python (FastAPI + Pydantic) · SQLAlchemy + Alembic · SQLite (dev) / PostgreSQL (prod) · NumPy/SciPy for the statistics · Docker + Docker Compose.

```
client → FastAPI routes → ABTestFramework.route_request()
                                │
                    ┌───────────┴───────────┐
                    │                       │
            StorageBackend           model registry → adapter (http | python_callable)
         (InMemory | Database)              │
                    │                  real model call
                    └───────────┬───────────┘
                                │
                     statistics engine (Welch's t-test, CI, effect size)
                                │
                    GET /results, /timeseries
```

`src/statistics.py` and `src/adapters.py` are pure logic with no framework dependencies; `src/storage.py` is the persistence abstraction; `src/api/` is the FastAPI wiring on top. See `tests/` (74 tests, 83% coverage) for what's actually verified.

## License

MIT — see [LICENSE](LICENSE).
