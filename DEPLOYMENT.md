# Deployment Guide

## Prerequisites
- Docker + Docker Compose installed
- `.env.prod` file in project root (see `.env.example`)

## Start Production Stack

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

# Run DB backup (inside api container)
docker exec krisis-api-1 bash scripts/backup_db.sh

# Restore a backup
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
| GET | `/metrics` | App-level metrics |
| GET | `/metrics` (Prometheus) | Prometheus scrape endpoint |
| POST | `/api/v1/experiments` | Create experiment |
| GET | `/api/v1/experiments` | List experiments |
| POST | `/api/v1/predict` | Route prediction |
| POST | `/api/v1/outcomes` | Record outcome |
| GET | `/api/v1/results/{id}` | Get results |
