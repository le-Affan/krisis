# Deployment Guide

## Prerequisites
- Docker + Docker Compose installed
- `.env.prod` file in project root (see `.env.example`)

## Quick Start (Recommended)

Use the all-in-one startup script to validate, build, and launch everything:

```bash
# Windows (CMD / PowerShell)
scripts\startup.bat

# Linux / macOS / Git Bash
./scripts/startup.sh

# Development mode
./scripts/startup.sh --dev

# Production + monitoring (Prometheus & Grafana)
./scripts/startup.sh --monitoring

# Force rebuild images
./scripts/startup.sh --rebuild

# Graceful shutdown
./scripts/startup.sh --down

# Shutdown + delete DB volumes
./scripts/startup.sh --down --purge
```

The script handles preflight checks, Docker builds, health-check polling, and prints
a status summary with access URLs when everything is ready.

## Local Dev/Test Stack (verified)

For local development or testing against a real Postgres (not the nginx/prod
stack below), use the plain `docker-compose.yml` — postgres + api only, no
`.env` file required:

```bash
docker compose up -d --build
```

Verified end-to-end: `db` becomes healthy, `api` connects to it as `db:5432`
over the compose network, runs Alembic migrations on startup, and serves on
`http://localhost:8000`. Confirm with:

```bash
curl http://localhost:8000/health
# {"status":"healthy","version":"1.0.0","storage_backend":"database"}
```

> **SELinux hosts (e.g. Fedora):** the `api` service bind-mounts `./src` and
> `./backups` with the `:z` label so the container can actually read/write
> them under an enforcing SELinux policy. Without it, the container fails
> with `ModuleNotFoundError: No module named 'src.api'` even though the files
> are clearly present on the host — SELinux is silently denying the read.

Tear down (and delete the DB volume) with:

```bash
docker compose down -v
```

## Start Production Stack (manual)

```bash
docker-compose -f docker-compose.prod.yml --env-file .env.prod up --build -d
```

Access the API at **http://localhost**

> **SSL (optional):** Place `cert.pem` and `key.pem` in `nginx/ssl/`, switch
> the nginx volume mount to `nginx/nginx.conf`, and uncomment port `443` in compose.

## Start Monitoring (optional)

```bash
docker-compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml --env-file .env.prod up -d
```

- Prometheus: http://localhost:9090
- Grafana:    http://localhost:3000  (admin / admin)

## Useful Commands

```bash
# Check status
docker-compose -f docker-compose.prod.yml ps

# View API logs
docker logs krisis-api-1 -f

# Run DB backup (inside api container) — data-only, schema comes from Alembic
docker exec krisis-api-1 bash scripts/backup_db.sh

# Restore a backup — target DB must already have the schema migrated
# (a normal api container startup does this automatically)
docker exec krisis-api-1 bash scripts/restore_db.sh /backups/backup_<timestamp>.sql.gz

# Apply new migrations only
docker exec krisis-api-1 alembic upgrade head

# Tear down (keeps DB volume)
docker-compose -f docker-compose.prod.yml down

# Tear down + delete DB data
docker-compose -f docker-compose.prod.yml down -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus scrape endpoint |
| GET | `/metrics/app` | App-level metrics (JSON: counts + uptime) |
| POST | `/api/v1/experiments` | Create experiment |
| GET | `/api/v1/experiments` | List experiments |
| GET | `/api/v1/experiments/{experiment_id}` | Get one experiment |
| PATCH | `/api/v1/experiments/{experiment_id}` | Update experiment status |
| POST | `/api/v1/predict` | Route prediction |
| POST | `/api/v1/outcomes` | Record outcome |
| GET | `/api/v1/experiments/{experiment_id}/results` | Get statistical results (incl. guardrail warnings) |
| POST | `/api/v1/sample-size-calculator` | Required sample size for a given effect |
| GET | `/api/v1/experiments/{experiment_id}/timeseries` | Cumulative stats bucketed over time |
| POST | `/api/v1/models` | Register a model (`http` or `python_callable` adapter) |
| GET | `/api/v1/models` | List registered models |
| GET | `/api/v1/models/{model_id}` | Get one registered model |

## Security Considerations

**The `python_callable` model adapter executes local code with no
sandboxing.** When a `python_callable` model is invoked, Krisis imports the
given module and calls the given function directly, in-process, with
whatever permissions the Krisis process itself has.

- **Never register a `python_callable` model on a Krisis deployment
  reachable by untrusted users.** Anyone who can reach `POST
  /api/v1/models` on such a deployment can get Krisis to import and execute
  arbitrary code already present on that machine's Python path — and if
  they can also influence what's importable there (e.g. a shared host,
  writable `PYTHONPATH`, or a compromised dependency), that's a direct path
  to remote code execution.
- `python_callable` is intended for **local, single-user development
  only** — which matches Krisis's current primary use case (one developer
  testing their own models on their own machine). There is no
  authentication on any Krisis endpoint by default, so treat
  `python_callable` as equivalent to giving API access = shell access.
- The **`http` adapter is the only adapter type safe for a
  multi-tenant or publicly-reachable deployment.** It only ever sends the
  input features as JSON to a URL over HTTP(S) — no local code execution.
- If you must expose Krisis beyond your own machine, either (a) restrict
  registration to `http`-only models at the network/proxy layer, or (b) put
  Krisis behind authentication so only trusted operators can call
  `POST /api/v1/models` at all. Neither is implemented by Krisis itself
  today — this is a deployment-time responsibility.
